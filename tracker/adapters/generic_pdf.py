from __future__ import annotations

from datetime import datetime
import re

from tracker.adapters.base import Adapter, AdapterInput
from tracker.pdftext import extract_pdf_text
from tracker.types import ParsedResult
from tracker.util import normalize_name


class GenericPdfResultsAdapter(Adapter):
    name = "generic_pdf_results"

    def can_handle(self, source_url: str, content_type: str, body: bytes) -> bool:
        return source_url.lower().endswith(".pdf") or "pdf" in content_type.lower()

    def discover_urls(self, payload: AdapterInput) -> list[str]:
        return []

    def parse_results(
        self,
        payload: AdapterInput,
        followed_athletes: set[str],
    ) -> list[ParsedResult]:
        text = extract_pdf_text(payload.body)
        return parse_generic_pdf_text(
            text,
            payload.fetched_url,
            followed_athletes,
            payload.fetched_at,
        )


def parse_generic_pdf_text(
    text: str,
    source_url: str,
    followed_athletes: set[str],
    captured_at: datetime,
) -> list[ParsedResult]:
    meet_name = "Public Results PDF"
    session_name = "Session"
    event_name = "Unknown Event"
    results: list[ParsedResult] = []

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
            event_name = ev.group(1).strip()
            continue

        row = line_re.match(line)
        if not row:
            continue

        athlete_name = row.group("name").strip()
        if normalize_name(athlete_name) not in followed_athletes:
            continue

        results.append(
            ParsedResult(
                source_url=source_url,
                meet_name=meet_name,
                session_name=session_name,
                event_name=event_name,
                athlete_name=athlete_name,
                club=row.group("club"),
                time_text=row.group("time"),
                captured_at=captured_at,
            )
        )

    return results
