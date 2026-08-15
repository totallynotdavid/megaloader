import ipaddress
import logging
import socket

from urllib.parse import quote, urlparse

import httpx

from fastapi import HTTPException, Request

from api.config import (
    ALLOWED_DOMAINS,
    RATE_LIMIT_REQUESTS,
    RATE_LIMIT_WINDOW,
    TRUST_PROXY_HEADERS,
    UNKNOWN_CLIENT,
    UPSTASH_REDIS_TOKEN,
    UPSTASH_REDIS_URL,
)


# ruff: noqa: TRY301 (FastAPI idiom: raise HTTPException directly)

logger = logging.getLogger(__name__)


def client_ip_from(request: Request) -> str:
    """
    Identify the caller for rate limiting.

    Uses the left-most X-Forwarded-For entry behind a trusted proxy, otherwise
    the socket address. Returns UNKNOWN_CLIENT when neither yields a valid IP,
    so a forged header can never widen the key space.
    """
    if TRUST_PROXY_HEADERS:
        forwarded = request.headers.get("x-forwarded-for", "")
        candidate = forwarded.split(",")[0].strip()
        if _is_ip_address(candidate):
            return candidate

    peer = request.client.host if request.client is not None else ""
    if _is_ip_address(peer):
        return peer

    return UNKNOWN_CLIENT


def _is_ip_address(value: str) -> bool:
    try:
        ipaddress.ip_address(value)
    except ValueError:
        return False
    return True


def validate_download_url(url: str) -> None:
    """
    Reject download URLs that point at non-public addresses.

    Download URLs come from upstream page content, so a compromised or hostile
    host could aim them at loopback or link-local addresses (cloud metadata
    endpoints, internal services) and turn the API into an SSRF proxy.

    Raises ValueError when the URL is not a fetchable public HTTP(S) address.
    """
    parsed = urlparse(url)

    if parsed.scheme not in ("http", "https"):
        msg = f"Refusing non-HTTP(S) download URL: {parsed.scheme or 'none'}"
        raise ValueError(msg)

    host = parsed.hostname
    if not host:
        msg = "Download URL has no host"
        raise ValueError(msg)

    try:
        infos = socket.getaddrinfo(host, parsed.port or 0, proto=socket.IPPROTO_TCP)
    except socket.gaierror as e:
        msg = f"Could not resolve download host: {host}"
        raise ValueError(msg) from e

    for info in infos:
        address = ipaddress.ip_address(info[4][0])
        if not address.is_global or address.is_multicast:
            msg = f"Refusing download from non-public address: {host}"
            raise ValueError(msg)


def validate_domain_whitelist(url: str) -> str:
    """
    Extract and validate domain against whitelist.

    Returns normalized domain if allowed.
    Raises HTTPException(403) if domain not whitelisted.
    """
    try:
        parsed = urlparse(url)

        if parsed.scheme not in ("http", "https"):
            raise HTTPException(400, "Only HTTP(S) URLs allowed")

        if not parsed.hostname:
            raise HTTPException(400, "Invalid URL format")

        # Credentials in the authority section make the host ambiguous to read
        # and serve no purpose for the supported platforms.
        if "@" in parsed.netloc:
            raise HTTPException(400, "Invalid URL format")

        domain = parsed.hostname.lower()

        if domain not in ALLOWED_DOMAINS:
            logger.warning(
                "Domain not whitelisted", extra={"domain": domain, "status_code": 403}
            )
            raise HTTPException(
                403,
                f"Domain '{domain}' not allowed. Supported: Bunkr, PixelDrain, Cyberdrop, GoFile",
            )

        return domain

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Domain validation failed")
        raise HTTPException(400, "Invalid URL format") from e


async def check_rate_limit(client_ip: str) -> None:
    """
    Check rate limit using Upstash Redis.

    Raises HTTPException(429) if limit exceeded.
    Skips check if Redis not configured (development).
    """
    if not UPSTASH_REDIS_URL or not UPSTASH_REDIS_TOKEN:
        logger.debug("Rate limiting disabled (no Redis configured)")
        return

    try:
        key = quote(f"ratelimit:{client_ip}", safe="")

        async with httpx.AsyncClient() as client:
            # Increment counter with expiry
            response = await client.post(
                f"{UPSTASH_REDIS_URL}/incr/{key}",
                headers={"Authorization": f"Bearer {UPSTASH_REDIS_TOKEN}"},
                timeout=2.0,
            )

            if response.status_code != 200:
                logger.warning("Redis request failed, allowing request")
                return

            data = response.json()
            count = data.get("result", 0)

            # Set expiry on first request
            if count == 1:
                await client.post(
                    f"{UPSTASH_REDIS_URL}/expire/{key}/{RATE_LIMIT_WINDOW}",
                    headers={"Authorization": f"Bearer {UPSTASH_REDIS_TOKEN}"},
                    timeout=2.0,
                )

            if count > RATE_LIMIT_REQUESTS:
                # Get TTL for retry-after
                ttl_response = await client.post(
                    f"{UPSTASH_REDIS_URL}/ttl/{key}",
                    headers={"Authorization": f"Bearer {UPSTASH_REDIS_TOKEN}"},
                    timeout=2.0,
                )

                retry_after = RATE_LIMIT_WINDOW
                if ttl_response.status_code == 200:
                    ttl_data = ttl_response.json()
                    retry_after = max(1, ttl_data.get("result", RATE_LIMIT_WINDOW))

                logger.warning(
                    "Rate limit exceeded",
                    extra={"client_ip": client_ip, "count": count, "status_code": 429},
                )

                raise HTTPException(
                    429,
                    f"Rate limit exceeded. Retry in {retry_after}s",
                    headers={"Retry-After": str(retry_after)},
                )

    except HTTPException:
        raise
    except Exception:
        logger.exception("Rate limit check failed, allowing request")
        return
