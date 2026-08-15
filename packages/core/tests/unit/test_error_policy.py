import pytest

from megaloader.error_policy import (
    build_extraction_error,
    classify_failure,
    raise_extraction_error,
    raise_for_api_status,
)
from megaloader.exceptions import ExtractionError


@pytest.mark.unit
def test_classify_failure_rate_limit_http() -> None:
    assert classify_failure(http_status=429) == "rate_limit"


@pytest.mark.unit
def test_classify_failure_auth_http() -> None:
    assert classify_failure(http_status=401) == "auth"


@pytest.mark.unit
def test_classify_failure_access_provider_status() -> None:
    assert classify_failure(provider_status="error-notPremium") == "access"


@pytest.mark.unit
def test_classify_failure_explicit_category_wins_over_signals() -> None:
    assert classify_failure(http_status=429, category="timeout") == "timeout"


@pytest.mark.unit
@pytest.mark.parametrize(
    ("provider_status", "expected"),
    [
        ("Error-RateLimit", "rate_limit"),
        ("error-notFound", "access"),
        ("error-passwordRequired", "access"),
        ("error-somethingElse", "unknown"),
    ],
)
def test_classify_failure_normalizes_provider_status(
    provider_status: str, expected: str
) -> None:
    assert classify_failure(provider_status=provider_status) == expected


@pytest.mark.unit
@pytest.mark.parametrize(
    ("http_status", "expected"), [(403, "access"), (404, "access")]
)
def test_classify_failure_access_http(http_status: int, expected: str) -> None:
    assert classify_failure(http_status=http_status) == expected


@pytest.mark.unit
def test_classify_failure_other_http_status_is_a_request_failure() -> None:
    assert classify_failure(http_status=500) == "request"


@pytest.mark.unit
def test_classify_failure_without_any_signal_is_unknown() -> None:
    assert classify_failure() == "unknown"


@pytest.mark.unit
def test_build_extraction_error_fields() -> None:
    err = build_extraction_error(
        "Failed request",
        source="pixiv",
        url="https://www.pixiv.net/ajax/illust/1",
        http_status=429,
        provider_status=None,
    )

    assert err.detail == "Failed request"
    assert err.source == "pixiv"
    assert err.url == "https://www.pixiv.net/ajax/illust/1"
    assert err.http_status == 429
    assert err.provider_status is None
    assert err.category == "rate_limit"
    assert str(err) == "Failed request"


@pytest.mark.unit
def test_build_extraction_error_keeps_the_original_cause() -> None:
    cause = ValueError("boom")

    err = build_extraction_error("wrapped", source="gofile", cause=cause)

    assert err.cause is cause
    assert err.category == "unknown"


@pytest.mark.unit
def test_raise_extraction_error_raises_the_built_error() -> None:
    with pytest.raises(ExtractionError) as exc_info:
        raise_extraction_error(
            "Failed request", source="pixiv", url="https://pixiv.net", http_status=401
        )

    assert exc_info.value.category == "auth"
    assert exc_info.value.source == "pixiv"


@pytest.mark.unit
def test_raise_for_api_status_accepts_ok() -> None:
    raise_for_api_status("gofile", "https://gofile.io", "ok")


@pytest.mark.unit
def test_raise_for_api_status_reports_the_provider_status() -> None:
    with pytest.raises(ExtractionError) as exc_info:
        raise_for_api_status("gofile", "https://gofile.io", "error-notFound")

    err = exc_info.value
    assert err.detail == "gofile API error: error-notFound"
    assert err.provider_status == "error-notFound"
    assert err.category == "access"


@pytest.mark.unit
def test_raise_for_api_status_appends_the_optional_message() -> None:
    with pytest.raises(ExtractionError, match=r"error-x \(bad token\)"):
        raise_for_api_status(
            "gofile", "https://gofile.io", "error-x", message="bad token"
        )
