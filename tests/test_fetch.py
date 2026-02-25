import pytest

import tracker.fetch as fetch
from tracker.fetch import FetchTooLargeError, _read_with_limit, classify_fetch_error


class _FakeResp:
    def __init__(self, chunks):
        self._chunks = list(chunks)

    def read(self, _size):
        if not self._chunks:
            return b""
        return self._chunks.pop(0)


def test_read_with_limit_raises_when_too_large() -> None:
    resp = _FakeResp([b"a" * 8, b"b" * 8])
    with pytest.raises(FetchTooLargeError) as exc:
        _read_with_limit(resp, max_bytes=10)
    assert exc.value.max_bytes == 10


def test_classify_fetch_too_large() -> None:
    err, code = classify_fetch_error(FetchTooLargeError(12345))
    assert err == "too_large:12345"
    assert code is None


class _FakeCtxResp:
    def __init__(self, text: str):
        self._text = text

    def read(self):
        return self._text.encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_robots_check_blocks_unsupported_scheme() -> None:
    allowed, reason = fetch.robots_check("file:///tmp/x", "ua", 1)
    assert not allowed
    assert reason == "unsupported_scheme"


def test_robots_check_blocks_when_robots_unavailable(monkeypatch) -> None:
    def _fail(*args, **kwargs):
        raise RuntimeError("network-down")

    monkeypatch.setattr(fetch, "urlopen", _fail)
    allowed, reason = fetch.robots_check("https://example.com/path", "ua", 1)
    assert not allowed
    assert reason == "robots_unavailable:RuntimeError"


def test_robots_check_respects_disallow(monkeypatch) -> None:
    monkeypatch.setattr(
        fetch,
        "urlopen",
        lambda *args, **kwargs: _FakeCtxResp("User-agent: *\nDisallow: /\n"),
    )
    allowed, reason = fetch.robots_check("https://example.com/path", "ua", 1)
    assert not allowed
    assert reason == "robots_disallow"
