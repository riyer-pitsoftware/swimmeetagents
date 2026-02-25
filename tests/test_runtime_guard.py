import pytest

import tracker.runtime_guard as runtime_guard


def test_runtime_guard_blocks_host(monkeypatch) -> None:
    monkeypatch.delenv("TRACKER_ALLOW_HOST", raising=False)
    monkeypatch.delenv("TRACKER_CONTAINER", raising=False)
    monkeypatch.setattr(runtime_guard.Path, "exists", lambda self: False)

    with pytest.raises(RuntimeError):
        runtime_guard.require_container_runtime()


def test_runtime_guard_allows_container_env(monkeypatch) -> None:
    monkeypatch.setenv("TRACKER_CONTAINER", "1")
    monkeypatch.setattr(runtime_guard.Path, "exists", lambda self: False)
    runtime_guard.require_container_runtime()
