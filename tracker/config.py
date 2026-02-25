from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppConfig:
    db_path: Path
    sources_file: Path
    poll_seconds: int = 900
    min_poll_seconds: int = 600
    max_backoff_seconds: int = 7200
    http_timeout_seconds: int = 15
    max_download_bytes: int = 20 * 1024 * 1024
    user_agent: str = "swim-tracker-personal/0.1 (+local personal use)"

    @classmethod
    def load(cls) -> AppConfig:
        db_path = Path(os.getenv("TRACKER_DB_PATH", ".data/tracker.db"))
        sources_file = Path(os.getenv("TRACKER_SOURCES_FILE", "./sources.md"))
        poll_seconds = int(os.getenv("TRACKER_POLL_SECONDS", "900"))
        min_poll_seconds = int(os.getenv("TRACKER_MIN_POLL_SECONDS", "600"))
        max_backoff_seconds = int(os.getenv("TRACKER_MAX_BACKOFF_SECONDS", "7200"))
        http_timeout_seconds = int(os.getenv("TRACKER_HTTP_TIMEOUT_SECONDS", "15"))
        max_download_bytes = int(os.getenv("TRACKER_MAX_DOWNLOAD_BYTES", str(20 * 1024 * 1024)))
        user_agent = os.getenv(
            "TRACKER_USER_AGENT",
            "swim-tracker-personal/0.1 (+local personal use)",
        )

        if poll_seconds < min_poll_seconds:
            poll_seconds = min_poll_seconds
        if min_poll_seconds < 600:
            min_poll_seconds = 600
        if max_backoff_seconds < min_poll_seconds:
            max_backoff_seconds = min_poll_seconds
        if max_download_bytes < 1024:
            max_download_bytes = 1024

        return cls(
            db_path=db_path,
            sources_file=sources_file,
            poll_seconds=poll_seconds,
            min_poll_seconds=min_poll_seconds,
            max_backoff_seconds=max_backoff_seconds,
            http_timeout_seconds=http_timeout_seconds,
            max_download_bytes=max_download_bytes,
            user_agent=user_agent,
        )
