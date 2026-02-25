import os

from tracker.config import AppConfig


def test_max_download_bytes_has_minimum_floor() -> None:
    old = os.environ.get("TRACKER_MAX_DOWNLOAD_BYTES")
    try:
        os.environ["TRACKER_MAX_DOWNLOAD_BYTES"] = "1"
        cfg = AppConfig.load()
        assert cfg.max_download_bytes == 1024
    finally:
        if old is None:
            os.environ.pop("TRACKER_MAX_DOWNLOAD_BYTES", None)
        else:
            os.environ["TRACKER_MAX_DOWNLOAD_BYTES"] = old
