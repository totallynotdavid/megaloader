import logging

from urllib.parse import urlparse

import httpx

from fastapi import HTTPException

from api.config import (
    ALLOWED_DOMAINS,
    RATE_LIMIT_REQUESTS,
    RATE_LIMIT_WINDOW,
    UPSTASH_REDIS_TOKEN,
    UPSTASH_REDIS_URL,
)


# ruff: noqa: TRY301 (FastAPI idiom: raise HTTPException directly)

logger = logging.getLogger(__name__)


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

        if not parsed.netloc:
            raise HTTPException(400, "Invalid URL format")

        domain = parsed.netloc.lower()

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
        key = f"ratelimit:{client_ip}"

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
