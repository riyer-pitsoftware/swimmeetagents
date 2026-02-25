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


def is_domain_blocked(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    return any(bad in host for bad in BLOCKED_HOST_SUBSTRINGS)


def robots_allow(url: str, user_agent: str, timeout_seconds: int) -> bool:
    parsed = urlparse(url)
    robots_url = urljoin(f"{parsed.scheme}://{parsed.netloc}", "/robots.txt")
    rp = RobotFileParser()
    try:
        req = Request(robots_url, headers={"User-Agent": user_agent})
        with urlopen(req, timeout=timeout_seconds) as resp:
            data = resp.read().decode("utf-8", errors="replace")
            rp.parse(data.splitlines())
    except Exception:
        # Conservative fallback: unknown robots is treated as allow for now.
        return True
    return rp.can_fetch(user_agent, url)


def fetch_url(url: str, user_agent: str, timeout_seconds: int) -> FetchResponse:
    req = Request(url, headers={"User-Agent": user_agent})
    with urlopen(req, timeout=timeout_seconds) as resp:
        content_type = resp.headers.get("Content-Type", "application/octet-stream")
        return FetchResponse(
            url=url,
            status_code=getattr(resp, "status", 200),
            content_type=content_type,
            body=resp.read(),
        )


def classify_fetch_error(exc: Exception) -> tuple[str, int | None]:
    if isinstance(exc, HTTPError):
        return (f"http_error:{exc.code}", exc.code)
    if isinstance(exc, URLError):
        return (f"url_error:{exc.reason}", None)
    return (f"error:{type(exc).__name__}", None)
