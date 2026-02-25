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
    try:
        _read_with_limit(resp, max_bytes=10)
        assert False, "expected FetchTooLargeError"
    except FetchTooLargeError as exc:
        assert exc.max_bytes == 10


def test_classify_fetch_too_large() -> None:
    err, code = classify_fetch_error(FetchTooLargeError(12345))
    assert err == "too_large:12345"
    assert code is None
