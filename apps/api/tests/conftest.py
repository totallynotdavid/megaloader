import importlib
import os
import sys

from collections.abc import Callable, Iterator
from types import ModuleType
from urllib.parse import urlparse

import pytest

from fastapi.testclient import TestClient
from megaloader.item import DownloadItem

from tests.servers import Route, Server, UpstashStub


ENV_PREFIXES = ("API_", "UPSTASH_")
ENV_NAMES = ("VERCEL", "ENV")


@pytest.fixture(autouse=True)
def clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in list(os.environ):
        if name.startswith(ENV_PREFIXES) or name in ENV_NAMES:
            monkeypatch.delenv(name)


@pytest.fixture
def serve() -> Iterator[Callable[..., Server]]:
    servers: list[Server] = []

    def start(routes: dict[str, Route], *, public: bool = True) -> Server:
        server = Server(routes)
        server.start()
        servers.append(server)
        if public:
            PUBLIC_PORTS.add(server.port)
        return server

    yield start

    for server in servers:
        server.stop()
        PUBLIC_PORTS.discard(server.port)


@pytest.fixture
def upstash() -> Iterator[UpstashStub]:
    stub = UpstashStub()
    stub.start()
    yield stub
    stub.stop()


# Test servers live on loopback, which the download guard refuses by design.
# Ports registered here are treated as public; every other address, including
# other loopback ports, still goes through the real guard.
PUBLIC_PORTS: set[int] = set()


@pytest.fixture
def load_app(monkeypatch: pytest.MonkeyPatch) -> Callable[..., ModuleType]:
    """Import a fresh `index` module under the given environment."""

    def load(**env: str) -> ModuleType:
        for name, value in env.items():
            monkeypatch.setenv(name, value)
        for name in [m for m in sys.modules if m in ("index", "api")]:
            monkeypatch.delitem(sys.modules, name)
        for name in [m for m in sys.modules if m.startswith("api.")]:
            monkeypatch.delitem(sys.modules, name)

        index = importlib.import_module("index")
        allow_public_ports(monkeypatch)
        return index

    return load


def allow_public_ports(monkeypatch: pytest.MonkeyPatch) -> None:
    security = sys.modules["api.security"]
    real = getattr(security, "ensure_public_url", None)

    def guard(url: str) -> None:
        parsed = urlparse(url)
        if parsed.hostname == "127.0.0.1" and parsed.port in PUBLIC_PORTS:
            return
        if real is not None:
            real(url)

    monkeypatch.setattr(security, "ensure_public_url", guard, raising=False)


@pytest.fixture
def make_client() -> Callable[..., TestClient]:
    def make(index: ModuleType, host: str = "203.0.113.9") -> TestClient:
        return TestClient(
            index.app, client=(host, 50000), raise_server_exceptions=False
        )

    return make


@pytest.fixture
def stub_extraction(monkeypatch: pytest.MonkeyPatch) -> Callable[..., None]:
    """Make /download extract the given items instead of asking a live host."""

    def stub(index: ModuleType, items: list[DownloadItem]) -> None:
        monkeypatch.setattr(index, "extract_items", lambda url, domain: items)

    return stub


DOWNLOAD_BODY = {"url": "https://pixeldrain.com/l/abc"}
