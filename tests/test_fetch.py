from urllib.request import Request

import pytest

import tracker.fetch as fetch
from tracker.fetch import (
    BlockedTargetError,
    FetchTooLargeError,
    _read_with_limit,
    _SafeRedirectHandler,
    classify_fetch_error,
    is_target_blocked,
)


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

    monkeypatch.setattr(fetch, "_open_with_safe_redirects", _fail)
    allowed, reason = fetch.robots_check("https://example.com/path", "ua", 1)
    assert not allowed
    assert reason == "robots_unavailable:RuntimeError"


def test_robots_check_respects_disallow(monkeypatch) -> None:
    monkeypatch.setattr(
        fetch,
        "_open_with_safe_redirects",
        lambda *args, **kwargs: _FakeCtxResp("User-agent: *\nDisallow: /\n"),
    )
    allowed, reason = fetch.robots_check("https://example.com/path", "ua", 1)
    assert not allowed
    assert reason == "robots_disallow"


def test_target_blocked_for_localhost() -> None:
    blocked, reason = is_target_blocked("http://localhost:8787/")
    assert blocked
    assert reason == "local_hostname_blocked"


def test_target_blocked_for_private_ip() -> None:
    blocked, reason = is_target_blocked("http://192.168.1.10/path")
    assert blocked
    assert reason == "private_ip_blocked"


def test_target_blocked_for_non_standard_port() -> None:
    blocked, reason = is_target_blocked("https://example.com:8443/path")
    assert blocked
    assert reason == "non_standard_port_blocked"


def test_target_allows_standard_https_port() -> None:
    blocked, reason = is_target_blocked("https://example.com:443/path")
    assert not blocked
    assert reason is None


def test_target_blocked_for_resolved_private_ip(monkeypatch) -> None:
    monkeypatch.setattr(
        fetch.socket,
        "getaddrinfo",
        lambda *args, **kwargs: [
            (fetch.socket.AF_INET, fetch.socket.SOCK_STREAM, 0, "", ("10.0.0.9", 0))
        ],
    )
    blocked, reason = is_target_blocked("http://example.com/path")
    assert blocked
    assert reason == "resolved_private_ip_blocked"


def test_classify_fetch_blocked_target() -> None:
    err, code = classify_fetch_error(BlockedTargetError("http://localhost", "local"))
    assert err == "target_blocked:local"
    assert code is None


def test_redirect_handler_blocks_unsafe_redirect(monkeypatch) -> None:
    monkeypatch.setattr(fetch, "is_target_blocked", lambda u: (True, "private_ip_blocked"))
    handler = _SafeRedirectHandler()
    req = Request("https://example.com/start")
    with pytest.raises(BlockedTargetError) as exc:
        handler.redirect_request(req, None, 302, "Found", {}, "https://10.0.0.5/next")
    assert exc.value.reason == "redirect_private_ip_blocked"


def test_redirect_handler_allows_safe_redirect(monkeypatch) -> None:
    monkeypatch.setattr(fetch, "is_target_blocked", lambda u: (False, None))
    handler = _SafeRedirectHandler()
    req = Request("https://example.com/start")
    redirected = handler.redirect_request(req, None, 302, "Found", {}, "https://example.com/next")
    assert redirected is not None
    assert redirected.full_url == "https://example.com/next"
