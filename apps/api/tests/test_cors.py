from collections.abc import Callable
from types import ModuleType

from fastapi.testclient import TestClient


PREFLIGHT = {
    "Access-Control-Request-Method": "POST",
    "Access-Control-Request-Headers": "content-type",
}


def preflight(client: TestClient, origin: str):
    return client.options("/download", headers={"Origin": origin, **PREFLIGHT})


def test_wildcard_origin_never_allows_credentials(
    load_app: Callable[..., ModuleType], make_client: Callable[..., TestClient]
) -> None:
    client = make_client(load_app(API_CORS_ORIGINS="*"))

    response = preflight(client, "https://evil.example")

    assert response.status_code == 200
    assert "access-control-allow-credentials" not in response.headers
    assert response.headers["access-control-allow-origin"] == "*"


def test_default_config_never_allows_credentials(
    load_app: Callable[..., ModuleType], make_client: Callable[..., TestClient]
) -> None:
    client = make_client(load_app())

    response = preflight(client, "https://evil.example")

    assert "access-control-allow-credentials" not in response.headers


def test_explicit_origin_allows_credentials(
    load_app: Callable[..., ModuleType], make_client: Callable[..., TestClient]
) -> None:
    client = make_client(load_app(API_CORS_ORIGINS="https://app.example"))

    response = preflight(client, "https://app.example")

    assert response.headers["access-control-allow-origin"] == "https://app.example"
    assert response.headers["access-control-allow-credentials"] == "true"


def test_explicit_list_rejects_other_origins(
    load_app: Callable[..., ModuleType], make_client: Callable[..., TestClient]
) -> None:
    client = make_client(load_app(API_CORS_ORIGINS="https://app.example"))

    response = preflight(client, "https://evil.example")

    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers


def test_wildcard_inside_list_still_disables_credentials(
    load_app: Callable[..., ModuleType], make_client: Callable[..., TestClient]
) -> None:
    client = make_client(load_app(API_CORS_ORIGINS="https://app.example, *"))

    response = preflight(client, "https://evil.example")

    assert "access-control-allow-credentials" not in response.headers
