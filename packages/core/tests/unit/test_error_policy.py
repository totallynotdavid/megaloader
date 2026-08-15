import pytest

from megaloader.error_policy import (
    build_extraction_error,
    classify_failure,
    raise_extraction_error,
    raise_for_api_status,
)
from megaloader.exceptions import ExtractionError


@pytest.mark.unit
@pytest.mark.parametrize(
    ("http_status", "provider_status", "category", "expected"),
    [
        pytest.param(429, None, None, "rate_limit", id="http-429"),
        pytest.param(401, None, None, "auth", id="http-401"),
        pytest.param(403, None, None, "access", id="http-403"),
        pytest.param(404, None, None, "access", id="http-404"),
        pytest.param(500, None, None, "request", id="http-500"),
        pytest.param(
            None, "Error-RateLimit", None, "rate_limit", id="provider-throttle"
        ),
        pytest.param(None, "error-notFound", None, "access", id="provider-missing"),
        pytest.param(
            None, "error-passwordRequired", None, "access", id="provider-locked"
        ),
        pytest.param(None, "error-notPremium", None, "access", id="provider-paywalled"),
        pytest.param(
            None, "error-somethingElse", None, "unknown", id="unknown-provider-status"
        ),
        pytest.param(None, None, None, "unknown", id="no-signal"),
        # Callers that already know what went wrong are not second-guessed.
        pytest.param(429, None, "timeout", "timeout", id="explicit-wins"),
    ],
)
def test_a_failure_is_classified_from_whatever_signals_are_available(
    http_status: int | None,
    provider_status: str | None,
    category: str | None,
    expected: str,
) -> None:
    assert (
        classify_failure(
            http_status=http_status,
            provider_status=provider_status,
            category=category,
        )
        == expected
    )


@pytest.mark.unit
def test_a_built_error_carries_the_context_needed_to_act_on_it() -> None:
    cause = ValueError("boom")

    err = build_extraction_error(
        "Failed request",
        source="pixiv",
        url="https://www.pixiv.net/ajax/illust/1",
        http_status=429,
        cause=cause,
    )

    assert str(err) == "Failed request"
    assert err.source == "pixiv"
    assert err.url == "https://www.pixiv.net/ajax/illust/1"
    assert err.http_status == 429
    assert err.category == "rate_limit"
    assert err.cause is cause


@pytest.mark.unit
def test_raising_a_failure_produces_that_same_classified_error() -> None:
    with pytest.raises(ExtractionError) as exc_info:
        raise_extraction_error(
            "Failed request", source="pixiv", url="https://pixiv.net", http_status=401
        )

    assert exc_info.value.category == "auth"
    assert exc_info.value.source == "pixiv"


@pytest.mark.unit
def test_an_ok_api_status_is_not_a_failure() -> None:
    raise_for_api_status("gofile", "https://gofile.io", "ok")


@pytest.mark.unit
def test_a_failing_api_status_becomes_a_readable_classified_error() -> None:
    with pytest.raises(ExtractionError) as exc_info:
        raise_for_api_status(
            "gofile", "https://gofile.io", "error-notFound", message="no such link"
        )

    err = exc_info.value
    assert err.detail == "gofile API error: error-notFound (no such link)"
    assert err.provider_status == "error-notFound"
    assert err.category == "access"
