from typing import Never

from megaloader.exceptions import ExtractionError


def classify_failure(
    http_status: int | None = None,
    provider_status: str | None = None,
    *,
    category: str | None = None,
) -> str:
    if category:
        return category

    normalized_provider = (provider_status or "").lower()
    if http_status == 429 or normalized_provider == "error-ratelimit":
        return "rate_limit"
    if http_status == 401:
        return "auth"
    if http_status in {403, 404}:
        return "access"
    if normalized_provider in {
        "error-notpremium",
        "error-notfound",
        "error-passwordrequired",
    }:
        return "access"
    if http_status is not None:
        return "request"
    if provider_status is not None:
        return "unknown"
    return "unknown"


def build_extraction_error(
    detail: str,
    *,
    source: str | None = None,
    url: str | None = None,
    http_status: int | None = None,
    provider_status: str | None = None,
    category: str | None = None,
    cause: Exception | None = None,
) -> ExtractionError:
    return ExtractionError(
        detail,
        source=source,
        url=url,
        http_status=http_status,
        provider_status=provider_status,
        category=classify_failure(
            http_status=http_status,
            provider_status=provider_status,
            category=category,
        ),
        cause=cause,
    )


def raise_extraction_error(
    detail: str,
    *,
    source: str | None = None,
    url: str | None = None,
    http_status: int | None = None,
    provider_status: str | None = None,
    category: str | None = None,
    cause: Exception | None = None,
) -> Never:
    raise build_extraction_error(
        detail,
        source=source,
        url=url,
        http_status=http_status,
        provider_status=provider_status,
        category=category,
        cause=cause,
    )


def raise_for_api_status(
    source: str,
    url: str,
    status: str,
    *,
    message: str | None = None,
) -> None:
    if status == "ok":
        return

    detail = f"{source} API error: {status}"
    if message:
        detail = f"{detail} ({message})"
    raise_extraction_error(
        detail,
        source=source,
        url=url,
        provider_status=status,
    )
