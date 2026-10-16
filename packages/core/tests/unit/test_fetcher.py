import pytest
import requests
import requests_mock as req_mock

from megaloader.exceptions import ExtractionError
from megaloader.fetcher import Request, RequestsFetcher


URL = "https://example.com/data"


def _fetch() -> RequestsFetcher:
    return RequestsFetcher("dummyplugin")


@pytest.mark.unit
@pytest.mark.parametrize("method", ["GET", "POST"])
def test_returns_response_on_success(
    requests_mock: req_mock.Mocker, method: str
) -> None:
    requests_mock.register_uri(method, URL, text="ok")

    response = _fetch()(Request(URL, method=method))

    assert response.text == "ok"


@pytest.mark.unit
def test_http_error_carries_status_source_and_cause(
    requests_mock: req_mock.Mocker,
) -> None:
    requests_mock.get(URL, status_code=404)

    with pytest.raises(ExtractionError) as exc_info:
        _fetch()(Request(URL))

    err = exc_info.value
    assert err.http_status == 404
    assert err.category == "access"
    assert err.source == "dummyplugin"
    assert isinstance(err.__cause__, requests.HTTPError)


@pytest.mark.unit
@pytest.mark.parametrize(
    ("raised", "category"),
    [
        (requests.ConnectionError("refused"), "network"),
        (requests.Timeout("timed out"), "timeout"),
    ],
)
def test_transport_failure_is_classified(
    requests_mock: req_mock.Mocker, raised: Exception, category: str
) -> None:
    requests_mock.get(URL, exc=raised)

    with pytest.raises(ExtractionError) as exc_info:
        _fetch()(Request(URL))

    assert exc_info.value.category == category
