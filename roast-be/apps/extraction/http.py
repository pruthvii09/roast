import ipaddress
import socket
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from .exceptions import RemoteFetchError


def is_safe_public_url(url: str) -> bool:
    """
    SSRF guard for fetching a user-supplied URL server-side: only
    http/https, and every IP the hostname resolves to must not be
    private/loopback/link-local/reserved/multicast (blocks things like
    http://169.254.169.254/ or http://localhost/). Not airtight against
    DNS-rebinding (urlopen re-resolves at connect time rather than us
    pinning the checked IP) — a practical guard, not a bulletproof one.

    Only meaningful for URLs built from untrusted input (see
    apps.extraction.processors.website.WebsiteProcessor). Callers whose
    request target is a fixed, hardcoded host — never derived from
    submission.source_url — have no need for this check (see
    apps.extraction.processors.github.GitHubProcessor's docstring for
    why it deliberately doesn't call this).
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        return False
    try:
        addr_info = socket.getaddrinfo(parsed.hostname, None)
    except OSError:
        return False
    for *_rest, sockaddr in addr_info:
        ip = ipaddress.ip_address(sockaddr[0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            return False
    return True


@dataclass
class FetchedResponse:
    body: bytes
    content_type: str
    encoding: str | None


def fetch_url(
    url: str, *, timeout: float, max_bytes: int, headers: dict | None = None
) -> FetchedResponse:
    """
    Timeout-bounded GET, capped at max_bytes. Oversized responses are
    silently truncated rather than rejected — size limiting here is a
    resource guard, not a judgment on content quality — but any
    network/timeout/protocol error or non-2xx HTTP status raises
    RemoteFetchError, since those genuinely mean there's no usable
    content. Never logs the URL or response body — only used by callers
    (apps.extraction.processors.website/github) that wrap failures in
    their own clear, non-sensitive error messages.
    """
    request = Request(url, headers=headers or {})
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read(max_bytes + 1)
            content_type = response.headers.get_content_type()
            encoding = response.headers.get_content_charset()
    except HTTPError as exc:
        raise RemoteFetchError(f"Remote server returned HTTP {exc.code}.") from exc
    except (URLError, TimeoutError, OSError, ValueError) as exc:
        raise RemoteFetchError(
            "Failed to fetch remote content (network/timeout/protocol error)."
        ) from exc

    return FetchedResponse(body=raw[:max_bytes], content_type=content_type, encoding=encoding)
