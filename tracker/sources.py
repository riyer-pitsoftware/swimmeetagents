from __future__ import annotations

import argparse
import re
from pathlib import Path

from tracker.config import AppConfig
from tracker.db import Database
from tracker.runtime_guard import require_container_runtime
from tracker.types import SeedSource

LINE_RE = re.compile(r"\[(?P<tag>[^\]]+)\]\s+(?P<url>https?://\S+)")


def parse_sources_markdown(path: Path) -> list[SeedSource]:
    parsed: list[SeedSource] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue
        match = LINE_RE.search(line)
        if not match:
            continue
        tag = match.group("tag").strip()
        url = match.group("url").strip().rstrip(")")
        parsed.append(SeedSource(tag=tag, url=url))
    return parsed


def cmd_refresh(db: Database, sources_file: Path) -> int:
    sources = parse_sources_markdown(sources_file)
    db.upsert_seed_sources(sources)
    print(f"loaded {len(sources)} sources from {sources_file}")
    return 0


def cmd_list(db: Database) -> int:
    items = db.list_seed_sources()
    if not items:
        print("no seed sources in db")
        return 0
    for src in items:
        print(f"[{src.tag}] {src.url}")
    return 0


def main(argv: list[str] | None = None) -> int:
    require_container_runtime()
    parser = argparse.ArgumentParser(prog="python -m tracker.sources")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list")
    sub.add_parser("refresh")

    args = parser.parse_args(argv)
    config = AppConfig.load()
    db = Database(config.db_path)
    db.init_schema()
    try:
        if args.command == "refresh":
            return cmd_refresh(db, config.sources_file)
        if args.command == "list":
            return cmd_list(db)
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
