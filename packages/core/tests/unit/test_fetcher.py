import threading

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

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


class _AlwaysStatus(BaseHTTPRequestHandler):
    status = 429

    def do_GET(self) -> None:
        self.send_response(self.status)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def log_message(self, format: str, *args: object) -> None:
        pass


@pytest.mark.unit
@pytest.mark.block_network(allowed_hosts=["127.0.0.1"])
@pytest.mark.parametrize(
    ("status", "category"),
    [(429, "rate_limit"), (503, "request")],
)
def test_retried_status_keeps_its_classification_when_retries_run_out(
    monkeypatch: pytest.MonkeyPatch, status: int, category: str
) -> None:
    monkeypatch.setattr("megaloader.fetcher.RETRY_BACKOFF", 0)
    handler = type("Handler", (_AlwaysStatus,), {"status": status})
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with pytest.raises(ExtractionError) as exc_info:
            _fetch()(Request(f"http://127.0.0.1:{server.server_port}/"))
    finally:
        server.shutdown()
        server.server_close()
        thread.join()

    err = exc_info.value
    assert err.http_status == status
    assert err.category == category


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
