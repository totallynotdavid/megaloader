import pytest

from megaloader.error_policy import build_extraction_error, classify_failure


@pytest.mark.unit
@pytest.mark.parametrize(
    ("failure", "category"),
    [
        ({"http_status": 429}, "rate_limit"),
        ({"http_status": 401}, "auth"),
        ({"http_status": 403}, "access"),
        ({"http_status": 404}, "access"),
        ({"http_status": 500}, "request"),
        ({"provider_status": "error-ratelimit"}, "rate_limit"),
        ({"provider_status": "error-notPremium"}, "access"),
        ({"provider_status": "error-something-new"}, "unknown"),
        ({}, "unknown"),
        ({"http_status": 429, "category": "timeout"}, "timeout"),
    ],
)
def test_classify_failure(failure: dict[str, object], category: str) -> None:
    assert classify_failure(**failure) == category  # type: ignore[arg-type]


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
