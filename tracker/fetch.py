from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


BLOCKED_HOST_SUBSTRINGS = (
    "meetmobile",
)


@dataclass(frozen=True)
class FetchResponse:
    url: str
    status_code: int
    content_type: str
    body: bytes


class FetchTooLargeError(Exception):
    def __init__(self, max_bytes: int):
        self.max_bytes = max_bytes
        super().__init__(f"response exceeded max allowed bytes: {max_bytes}")


def is_domain_blocked(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    return any(bad in host for bad in BLOCKED_HOST_SUBSTRINGS)


def robots_check(
    url: str, user_agent: str, timeout_seconds: int
) -> tuple[bool, str | None]:
    parsed = urlparse(url)
    robots_url = urljoin(f"{parsed.scheme}://{parsed.netloc}", "/robots.txt")
    rp = RobotFileParser()
    try:
        req = Request(robots_url, headers={"User-Agent": user_agent})
        with urlopen(req, timeout=timeout_seconds) as resp:
            data = resp.read().decode("utf-8", errors="replace")
            rp.parse(data.splitlines())
    except Exception as exc:
        return (False, f"robots_unavailable:{type(exc).__name__}")

    if not rp.can_fetch(user_agent, url):
        return (False, "robots_disallow")
    return (True, None)


def fetch_url(
    url: str, user_agent: str, timeout_seconds: int, max_bytes: int
) -> FetchResponse:
    req = Request(url, headers={"User-Agent": user_agent})
    with urlopen(req, timeout=timeout_seconds) as resp:
        content_type = resp.headers.get("Content-Type", "application/octet-stream")
        body = _read_with_limit(resp, max_bytes=max_bytes)
        return FetchResponse(
            url=url,
            status_code=getattr(resp, "status", 200),
            content_type=content_type,
            body=body,
        )


def classify_fetch_error(exc: Exception) -> tuple[str, int | None]:
    if isinstance(exc, FetchTooLargeError):
        return (f"too_large:{exc.max_bytes}", None)
    if isinstance(exc, HTTPError):
        return (f"http_error:{exc.code}", exc.code)
    if isinstance(exc, URLError):
        return (f"url_error:{exc.reason}", None)
    return (f"error:{type(exc).__name__}", None)


def _read_with_limit(resp, max_bytes: int) -> bytes:
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = resp.read(64 * 1024)
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            raise FetchTooLargeError(max_bytes=max_bytes)
        chunks.append(chunk)
    return b"".join(chunks)
