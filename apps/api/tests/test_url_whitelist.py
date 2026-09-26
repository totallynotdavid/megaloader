from collections.abc import Callable
from types import ModuleType

import pytest

from fastapi.testclient import TestClient


@pytest.fixture
def client(
    load_app: Callable[..., ModuleType], make_client: Callable[..., TestClient]
) -> TestClient:
    return make_client(load_app())


def validate(client: TestClient, url: str):
    return client.post("/validate", json={"url": url})


@pytest.mark.parametrize(
    "url",
    [
        "https://pixeldrain.com/u/abc",
        "https://pixeldrain.com:443/u/abc",
        "http://pixeldrain.com:80/u/abc",
        "https://PixelDrain.com/u/abc",
    ],
)
def test_whitelisted_host_is_accepted_whatever_the_port_or_case(
    client: TestClient, url: str
) -> None:
    response = validate(client, url)

    assert response.status_code == 200
    assert response.json()["domain"] == "pixeldrain.com"


@pytest.mark.parametrize(
    "url",
    [
        "https://user@pixeldrain.com/u/abc",
        "https://user:pass@pixeldrain.com/u/abc",
        "https://pixeldrain.com@evil.example/u/abc",
        "https://pixeldrain.com:443@evil.example/u/abc",
        "https://evil.example\\@pixeldrain.com/u/abc",
    ],
)
def test_embedded_credentials_are_refused(client: TestClient, url: str) -> None:
    assert validate(client, url).status_code == 400


@pytest.mark.parametrize(
    "url",
    [
        "https://evil.example/u/abc",
        "https://pixeldrain.com.evil.example/u/abc",
        "https://evilpixeldrain.com/u/abc",
    ],
)
def test_other_hosts_are_forbidden(client: TestClient, url: str) -> None:
    assert validate(client, url).status_code == 403


def test_invalid_port_is_a_bad_request(client: TestClient) -> None:
    assert validate(client, "https://pixeldrain.com:abc/u/abc").status_code == 400


def test_non_http_scheme_is_a_bad_request(client: TestClient) -> None:
    assert validate(client, "ftp://pixeldrain.com/u/abc").status_code == 400
