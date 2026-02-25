from __future__ import annotations

import argparse
import time
from dataclasses import dataclass
from datetime import datetime
from urllib.parse import urlparse

from tracker.adapters import build_adapters
from tracker.adapters.base import AdapterInput
from tracker.config import AppConfig
from tracker.db import Database
from tracker.fetch import (
    classify_fetch_error,
    fetch_url,
)
from tracker.policy import evaluate_child_policy, evaluate_source_policy
from tracker.runtime_guard import require_container_runtime
from tracker.sources import parse_sources_markdown
from tracker.types import ParsedResult
from tracker.util import parse_swim_time_to_centiseconds


@dataclass
class SourceState:
    error_count: int = 0
    next_allowed_epoch: float = 0.0


@dataclass
class RunSummary:
    exit_code: int
    dry_run: bool
    source_count: int
    parsed_count: int
    inserted_count: int
    error_count: int
    blocked_count: int
    no_adapter_count: int


def choose_adapter(source_url: str, content_type: str, body: bytes):
    for adapter in build_adapters():
        if adapter.can_handle(source_url, content_type, body):
            return adapter
    return None


def _print_timeline(db: Database, results: list[ParsedResult]) -> None:
    sorted_results = sorted(results, key=lambda r: (r.captured_at, r.athlete_name, r.event_name))
    for row in sorted_results:
        pb_before = db.latest_personal_best(row.athlete_name, row.event_name)
        cs = parse_swim_time_to_centiseconds(row.time_text)
        pb_flag = ""
        if cs is not None and (pb_before is None or cs <= pb_before):
            pb_flag = " PB"
        print(
            f"{row.captured_at.isoformat()} | {row.athlete_name} | {row.event_name} | {row.time_text}{pb_flag} | club={row.club or '-'}"
        )


def _process_url(
    db: Database,
    config: AppConfig,
    source_url: str,
    followed: set[str],
    dry_run: bool,
) -> dict[str, int]:
    print(f"processing source: {source_url}")
    source_policy = evaluate_source_policy(
        source_url, config.user_agent, config.http_timeout_seconds
    )
    if not source_policy.allowed:
        db.log_fetch(
            source_url,
            status="blocked",
            error=source_policy.reason or "policy_blocked",
        )
        print(f"skip source by policy: {source_url} reason={source_policy.reason}")
        return {"inserted": 0, "parsed": 0, "errors": 1, "blocked": 1, "no_adapter": 0}

    try:
        resp = fetch_url(
            source_url,
            config.user_agent,
            config.http_timeout_seconds,
            config.max_download_bytes,
        )
    except Exception as exc:
        err, code = classify_fetch_error(exc)
        db.log_fetch(source_url, status="error", http_status=code, error=err)
        print(f"fetch error for {source_url}: {err}")
        return {"inserted": 0, "parsed": 0, "errors": 1, "blocked": 0, "no_adapter": 0}

    db.log_fetch(source_url, status="ok", http_status=resp.status_code)
    payload = AdapterInput(
        source_url=source_url,
        fetched_url=resp.url,
        content_type=resp.content_type,
        body=resp.body,
        fetched_at=datetime.utcnow(),
    )
    adapter = choose_adapter(source_url, resp.content_type, resp.body)
    if adapter is None:
        print(f"no adapter for {source_url}")
        return {"inserted": 0, "parsed": 0, "errors": 0, "blocked": 0, "no_adapter": 1}

    parsed_results = adapter.parse_results(payload, followed)

    # Discover one-level children (light traffic).
    for child in adapter.discover_urls(payload)[:8]:
        if urlparse(child).scheme not in ("http", "https"):
            continue
        child_policy = evaluate_child_policy(
            child,
            config.user_agent,
            config.http_timeout_seconds,
        )
        if not child_policy.allowed:
            db.log_fetch(child, status="blocked", error=child_policy.reason or "blocked_target")
            print(f"skip blocked child target: {child} reason={child_policy.reason}")
            continue
        try:
            c_resp = fetch_url(
                child,
                config.user_agent,
                config.http_timeout_seconds,
                config.max_download_bytes,
            )
            c_adapter = choose_adapter(child, c_resp.content_type, c_resp.body)
            if c_adapter is None:
                continue
            child_payload = AdapterInput(
                source_url=source_url,
                fetched_url=child,
                content_type=c_resp.content_type,
                body=c_resp.body,
                fetched_at=datetime.utcnow(),
            )
            parsed_results.extend(c_adapter.parse_results(child_payload, followed))
        except Exception as exc:
            print(f"child fetch/parse skipped for {child}: {type(exc).__name__}")

    if dry_run:
        _print_timeline(db, parsed_results)
        return {
            "inserted": 0,
            "parsed": len(parsed_results),
            "errors": 0,
            "blocked": 0,
            "no_adapter": 0,
        }

    inserted = db.insert_results(parsed_results)
    _print_timeline(db, parsed_results)
    return {
        "inserted": inserted,
        "parsed": len(parsed_results),
        "errors": 0,
        "blocked": 0,
        "no_adapter": 0,
    }


def _load_sources(db: Database, config: AppConfig, extra_urls: list[str]) -> list[str]:
    seeds = parse_sources_markdown(config.sources_file)
    db.upsert_seed_sources(seeds, deactivate_missing=True)
    urls = [s.url for s in db.list_seed_sources()]
    urls.extend(extra_urls)
    return sorted(set(urls))


def run_once_with_summary(
    db: Database,
    config: AppConfig,
    extra_urls: list[str],
    dry_run: bool,
) -> RunSummary:
    followed = {a.normalized_name for a in db.list_athletes()}
    if not followed:
        print('no athletes configured; add with: python -m tracker.athletes add "Name"')
        return RunSummary(
            exit_code=2,
            dry_run=dry_run,
            source_count=0,
            parsed_count=0,
            inserted_count=0,
            error_count=1,
            blocked_count=0,
            no_adapter_count=0,
        )

    sources = _load_sources(db, config, extra_urls)
    inserted_total = 0
    parsed_total = 0
    errors_total = 0
    blocked_total = 0
    no_adapter_total = 0
    for source_url in sources:
        stats = _process_url(db, config, source_url, followed, dry_run)
        inserted_total += stats["inserted"]
        parsed_total += stats["parsed"]
        errors_total += stats["errors"]
        blocked_total += stats["blocked"]
        no_adapter_total += stats["no_adapter"]

    exit_code = 0 if errors_total == 0 else 1
    print(
        "run complete:"
        f" sources={len(sources)} parsed={parsed_total} inserted={inserted_total}"
        f" no_adapter={no_adapter_total} blocked={blocked_total}"
        f" errors={errors_total} dry_run={dry_run}"
    )
    return RunSummary(
        exit_code=exit_code,
        dry_run=dry_run,
        source_count=len(sources),
        parsed_count=parsed_total,
        inserted_count=inserted_total,
        error_count=errors_total,
        blocked_count=blocked_total,
        no_adapter_count=no_adapter_total,
    )


def run_once(db: Database, config: AppConfig, extra_urls: list[str], dry_run: bool) -> int:
    return run_once_with_summary(db, config, extra_urls, dry_run).exit_code


def run_watch(db: Database, config: AppConfig, extra_urls: list[str], dry_run: bool) -> int:
    states: dict[str, SourceState] = {}
    sources = _load_sources(db, config, extra_urls)
    for src in sources:
        states[src] = SourceState()

    while True:
        followed = {a.normalized_name for a in db.list_athletes()}
        now = time.time()
        for source_url in sources:
            state = states[source_url]
            if now < state.next_allowed_epoch:
                continue
            stats = _process_url(db, config, source_url, followed, dry_run)
            inserted = stats["inserted"]
            errs = stats["errors"]
            if errs:
                state.error_count += 1
                delay = min(
                    config.max_backoff_seconds, config.poll_seconds * (2**state.error_count)
                )
                state.next_allowed_epoch = time.time() + delay
                db.log_fetch(source_url, status="backoff", backoff_seconds=delay)
            else:
                state.error_count = 0
                state.next_allowed_epoch = time.time() + config.poll_seconds
            print(
                f"source={source_url} inserted={inserted} next_check_in={int(state.next_allowed_epoch - time.time())}s"
            )
        time.sleep(2)


def main(argv: list[str] | None = None) -> int:
    require_container_runtime()
    parser = argparse.ArgumentParser(prog="python -m tracker.run")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--once", action="store_true")
    mode.add_argument("--watch", action="store_true")
    parser.add_argument(
        "--dry-run", action="store_true", help="parse and print results without DB writes"
    )
    parser.add_argument(
        "--source-url", action="append", default=[], help="additional custom source URL"
    )

    args = parser.parse_args(argv)
    config = AppConfig.load()
    db = Database(config.db_path)
    db.init_schema()
    try:
        if args.once:
            return run_once(db, config, args.source_url, args.dry_run)
        return run_watch(db, config, args.source_url, args.dry_run)
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
