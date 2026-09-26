from collections.abc import Callable
from types import ModuleType

import pytest

from fastapi.testclient import TestClient

from tests.servers import UpstashStub


VALIDATE = {"url": "https://pixeldrain.com/u/abc"}


def limited_app(
    load_app: Callable[..., ModuleType], upstash: UpstashStub, **env: str
) -> ModuleType:
    return load_app(
        UPSTASH_REDIS_REST_URL=upstash.base_url,
        UPSTASH_REDIS_REST_TOKEN="token",
        API_RATE_LIMIT_REQUESTS="2",
        **env,
    )


def forwarded(client: TestClient, address: str):
    return client.post("/validate", json=VALIDATE, headers={"X-Forwarded-For": address})


def test_forwarded_callers_get_separate_buckets_on_vercel(
    load_app: Callable[..., ModuleType],
    make_client: Callable[..., TestClient],
    upstash: UpstashStub,
) -> None:
    client = make_client(limited_app(load_app, upstash, VERCEL="1"), host="76.76.21.1")

    statuses = [forwarded(client, "198.51.100.1").status_code for _ in range(3)]
    other_caller = forwarded(client, "198.51.100.2")

    assert statuses == [200, 200, 429]
    assert other_caller.status_code == 200
    assert "/incr/ratelimit:198.51.100.1" in upstash.paths


def test_left_most_forwarded_address_is_the_caller(
    load_app: Callable[..., ModuleType],
    make_client: Callable[..., TestClient],
    upstash: UpstashStub,
) -> None:
    client = make_client(limited_app(load_app, upstash, VERCEL="1"))

    forwarded(client, "198.51.100.1, 10.0.0.1, 76.76.21.1")

    assert upstash.paths[0] == "/incr/ratelimit:198.51.100.1"


def test_forwarded_header_is_ignored_without_trusted_proxy(
    load_app: Callable[..., ModuleType],
    make_client: Callable[..., TestClient],
    upstash: UpstashStub,
) -> None:
    client = make_client(limited_app(load_app, upstash), host="203.0.113.9")

    statuses = [forwarded(client, f"198.51.100.{n}").status_code for n in range(3)]

    assert statuses == [200, 200, 429]
    assert upstash.paths[0] == "/incr/ratelimit:203.0.113.9"


def test_trust_can_be_switched_off_on_vercel(
    load_app: Callable[..., ModuleType],
    make_client: Callable[..., TestClient],
    upstash: UpstashStub,
) -> None:
    app = limited_app(load_app, upstash, VERCEL="1", API_TRUST_PROXY="false")
    client = make_client(app, host="203.0.113.9")

    forwarded(client, "198.51.100.1")

    assert upstash.paths[0] == "/incr/ratelimit:203.0.113.9"


def test_trust_can_be_switched_on_outside_vercel(
    load_app: Callable[..., ModuleType],
    make_client: Callable[..., TestClient],
    upstash: UpstashStub,
) -> None:
    client = make_client(limited_app(load_app, upstash, API_TRUST_PROXY="true"))

    forwarded(client, "198.51.100.1")

    assert upstash.paths[0] == "/incr/ratelimit:198.51.100.1"


@pytest.mark.parametrize(
    "value",
    ["not-an-ip", "198.51.100.1/../../flushall", "198.51.100.1?x=1", "", "999.1.1.1"],
)
def test_invalid_forwarded_address_falls_back_to_socket_address(
    load_app: Callable[..., ModuleType],
    make_client: Callable[..., TestClient],
    upstash: UpstashStub,
    value: str,
) -> None:
    client = make_client(limited_app(load_app, upstash, VERCEL="1"), host="203.0.113.9")

    forwarded(client, value)

    assert upstash.paths[0] == "/incr/ratelimit:203.0.113.9"


def test_ipv6_forwarded_address_is_a_valid_caller(
    load_app: Callable[..., ModuleType],
    make_client: Callable[..., TestClient],
    upstash: UpstashStub,
) -> None:
    client = make_client(limited_app(load_app, upstash, VERCEL="1"))

    forwarded(client, "2001:db8::1")

    assert upstash.paths[0] == "/incr/ratelimit:2001:db8::1"


def test_socket_address_is_quoted_into_the_redis_path(
    load_app: Callable[..., ModuleType],
    make_client: Callable[..., TestClient],
    upstash: UpstashStub,
) -> None:
    client = make_client(limited_app(load_app, upstash), host="a/b?c#d e")

    client.post("/validate", json=VALIDATE)

    assert upstash.paths[0] == "/incr/ratelimit:a%2Fb%3Fc%23d%20e"
