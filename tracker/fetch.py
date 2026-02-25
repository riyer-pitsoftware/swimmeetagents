from __future__ import annotations

import ipaddress
import socket
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener
from urllib.robotparser import RobotFileParser

BLOCKED_HOST_SUBSTRINGS = ("meetmobile",)


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


class BlockedTargetError(Exception):
    def __init__(self, url: str, reason: str):
        self.url = url
        self.reason = reason
        super().__init__(f"blocked target {url}: {reason}")


def is_domain_blocked(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    return any(bad in host for bad in BLOCKED_HOST_SUBSTRINGS)


def is_target_blocked(url: str) -> tuple[bool, str | None]:
    parsed = urlparse(url)
    host = (parsed.hostname or "").strip().lower()
    if not host:
        return (True, "missing_host")
    if host in {"localhost", "localhost.localdomain"} or host.endswith(".local"):
        return (True, "local_hostname_blocked")
    if parsed.port is not None:
        if parsed.scheme == "http" and parsed.port != 80:
            return (True, "non_standard_port_blocked")
        if parsed.scheme == "https" and parsed.port != 443:
            return (True, "non_standard_port_blocked")

    blocked, reason = _block_reason_for_ip_literal(host)
    if blocked:
        return (True, reason)

    try:
        infos = socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
    except OSError:
        # If DNS lookup fails, fetch path will report a fetch error.
        return (False, None)

    for info in infos:
        addr = info[4][0]
        blocked, reason = _block_reason_for_ip_literal(addr)
        if blocked:
            return (True, f"resolved_{reason}")
    return (False, None)


def robots_check(url: str, user_agent: str, timeout_seconds: int) -> tuple[bool, str | None]:
    if not _is_http_scheme(url):
        return (False, "unsupported_scheme")
    blocked, reason = is_target_blocked(url)
    if blocked:
        return (False, reason)

    parsed = urlparse(url)
    robots_url = urljoin(f"{parsed.scheme}://{parsed.netloc}", "/robots.txt")
    rp = RobotFileParser()
    try:
        req = Request(robots_url, headers={"User-Agent": user_agent})
        with _open_with_safe_redirects(req, timeout_seconds=timeout_seconds) as resp:  # nosec B310
            data = resp.read().decode("utf-8", errors="replace")
            rp.parse(data.splitlines())
    except Exception as exc:
        return (False, f"robots_unavailable:{type(exc).__name__}")

    if not rp.can_fetch(user_agent, url):
        return (False, "robots_disallow")
    return (True, None)


def fetch_url(url: str, user_agent: str, timeout_seconds: int, max_bytes: int) -> FetchResponse:
    if not _is_http_scheme(url):
        raise ValueError("unsupported URL scheme")
    blocked, reason = is_target_blocked(url)
    if blocked:
        raise BlockedTargetError(url=url, reason=reason or "blocked_target")

    req = Request(url, headers={"User-Agent": user_agent})
    with _open_with_safe_redirects(req, timeout_seconds=timeout_seconds) as resp:  # nosec B310
        content_type = resp.headers.get("Content-Type", "application/octet-stream")
        body = _read_with_limit(resp, max_bytes=max_bytes)
        return FetchResponse(
            url=url,
            status_code=getattr(resp, "status", 200),
            content_type=content_type,
            body=body,
        )


def classify_fetch_error(exc: Exception) -> tuple[str, int | None]:
    if isinstance(exc, BlockedTargetError):
        return (f"target_blocked:{exc.reason}", None)
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


def _is_http_scheme(url: str) -> bool:
    return urlparse(url).scheme in ("http", "https")


def _block_reason_for_ip_literal(host: str) -> tuple[bool, str | None]:
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return (False, None)

    if ip.is_loopback:
        return (True, "loopback_ip_blocked")
    if ip.is_private:
        return (True, "private_ip_blocked")
    if ip.is_link_local:
        return (True, "link_local_ip_blocked")
    if ip.is_multicast:
        return (True, "multicast_ip_blocked")
    if ip.is_reserved:
        return (True, "reserved_ip_blocked")
    if ip.is_unspecified:
        return (True, "unspecified_ip_blocked")
    return (False, None)


class _SafeRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not _is_http_scheme(newurl):
            raise BlockedTargetError(newurl, "redirect_unsupported_scheme")
        blocked, reason = is_target_blocked(newurl)
        if blocked:
            raise BlockedTargetError(newurl, f"redirect_{reason}")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _open_with_safe_redirects(req: Request, timeout_seconds: int):
    opener = build_opener(_SafeRedirectHandler())
    return opener.open(req, timeout=timeout_seconds)
