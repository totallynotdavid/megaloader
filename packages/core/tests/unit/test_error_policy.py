import pytest

from megaloader.error_policy import build_extraction_error, classify_failure


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
