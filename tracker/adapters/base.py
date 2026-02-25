from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from tracker.types import ParsedResult


@dataclass(frozen=True)
class AdapterInput:
    source_url: str
    fetched_url: str
    content_type: str
    body: bytes
    fetched_at: datetime


class Adapter(Protocol):
    name: str

    def can_handle(self, source_url: str, content_type: str, body: bytes) -> bool:
        ...

    def discover_urls(self, payload: AdapterInput) -> list[str]:
        ...

    def parse_results(
        self,
        payload: AdapterInput,
        followed_athletes: set[str],
    ) -> list[ParsedResult]:
        ...
