from __future__ import annotations

from pathlib import Path
import os


def require_container_runtime() -> None:
    if os.getenv("TRACKER_ALLOW_HOST") == "1":
        return
    if os.getenv("TRACKER_CONTAINER") == "1":
        return
    if Path("/.dockerenv").exists():
        return
    raise RuntimeError(
        "Tracker is container-only. Run via Docker Compose, not directly on the host."
    )
