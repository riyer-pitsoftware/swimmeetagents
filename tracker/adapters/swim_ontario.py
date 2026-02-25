from __future__ import annotations

import re
from datetime import datetime
from html.parser import HTMLParser
from urllib.parse import urljoin

from tracker.adapters.base import Adapter, AdapterInput
from tracker.pdftext import extract_pdf_text
from tracker.types import ParsedResult
from tracker.util import normalize_name


class _LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        for k, v in attrs:
            if k.lower() == "href" and v:
                self.links.append(v)


class SwimOntarioAdapter(Adapter):
    name = "swim_ontario"

    def can_handle(self, source_url: str, content_type: str, body: bytes) -> bool:
        return "swimontario.com/liveresults" in source_url

    def discover_urls(self, payload: AdapterInput) -> list[str]:
        if "html" not in payload.content_type and not payload.source_url.endswith("/"):
            return []
        parser = _LinkParser()
        parser.feed(payload.body.decode("utf-8", errors="replace"))
        discovered: list[str] = []
        for href in parser.links:
            candidate = urljoin(payload.fetched_url, href)
            if (
                candidate.endswith(".pdf")
                or "ResultList_" in candidate
                or "results" in candidate.lower()
            ):
                discovered.append(candidate)
        return sorted(set(discovered))

    def parse_results(
        self,
        payload: AdapterInput,
        followed_athletes: set[str],
    ) -> list[ParsedResult]:
        text = payload.body.decode("utf-8", errors="replace")
        if payload.fetched_url.lower().endswith(".pdf") or "pdf" in payload.content_type:
            text = extract_pdf_text(payload.body)
        return _extract_results_from_text(
            text=text,
            source_url=payload.fetched_url,
            meet_name="Swim Ontario Meet",
            session_name="Live Results",
            followed_athletes=followed_athletes,
            captured_at=payload.fetched_at,
        )


def _extract_results_from_text(
    text: str,
    source_url: str,
    meet_name: str,
    session_name: str,
    followed_athletes: set[str],
    captured_at: datetime,
) -> list[ParsedResult]:
    results: list[ParsedResult] = []
    current_event = "Unknown Event"
    event_re = re.compile(r"(?:Event|EVENT)\s*\d+\s*[-:]?\s*(.+)$")
    line_re = re.compile(
        r"^(?P<name>[A-Za-z ,.'-]{3,}?)\s+(?:(?P<club>[A-Z]{2,6})\s+)?(?P<time>(?:\d+:)?\d{1,2}\.\d{2})\s*$"
    )

    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        ev = event_re.search(line)
        if ev:
            current_event = ev.group(1).strip()
            continue
        row = line_re.match(line)
        if not row:
            continue

        name = row.group("name").strip()
        normalized = normalize_name(name)
        if normalized not in followed_athletes:
            continue

        results.append(
            ParsedResult(
                source_url=source_url,
                meet_name=meet_name,
                session_name=session_name,
                event_name=current_event,
                athlete_name=name,
                club=row.group("club"),
                time_text=row.group("time"),
                captured_at=captured_at,
            )
        )
    return results
