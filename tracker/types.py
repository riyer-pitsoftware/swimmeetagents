from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class SeedSource:
    tag: str
    url: str


@dataclass(frozen=True)
class SourceContent:
    url: str
    content_type: str
    text: str | None
    binary: bytes | None


@dataclass(frozen=True)
class ParsedResult:
    source_url: str
    meet_name: str
    session_name: str
    event_name: str
    athlete_name: str
    club: str | None
    time_text: str
    captured_at: datetime
