from collections.abc import Callable
from types import ModuleType

import pytest
import requests

from tests.servers import Route, Server


def test_credentials_are_not_forwarded_to_another_host() -> None:
    from api.safe_http import headers_for_hop

    headers = {
        "Authorization": "Bearer x",
        "Cookie": "s=1",
        "Referer": "https://a.example/",
    }

    forwarded = headers_for_hop(headers, "https://a.example/f", "https://b.example/f")

    assert forwarded == {"Referer": "https://a.example/"}


@pytest.mark.parametrize(
    ("source", "target"),
    [
        ("https://a.example/f", "http://a.example/f"),
        ("https://a.example/f", "https://a.example:8443/f"),
        ("http://a.example:8080/f", "http://a.example:9090/f"),
        ("http://a.example:8080/f", "https://a.example:8080/f"),
        ("http://a.example/f", "https://a.example:8443/f"),
        ("https://a.example/f", "https://b.example/f"),
    ],
)
def test_credentials_are_stripped_unless_the_origin_matches(
    source: str, target: str
) -> None:
    from api.safe_http import headers_for_hop

    headers = {"Authorization": "Bearer x", "Cookie": "s=1", "Referer": source}

    assert headers_for_hop(headers, source, target) == {"Referer": source}


@pytest.mark.parametrize(
    ("source", "target"),
    [
        ("https://a.example/1", "https://a.example/2"),
        ("https://a.example/1", "https://a.example:443/2"),
        ("http://a.example:8080/1", "http://a.example:8080/2"),
        ("http://a.example/1", "https://a.example/2"),
        ("http://a.example:80/1", "https://a.example:443/2"),
    ],
)
def test_credentials_are_kept_within_an_origin_and_on_default_port_upgrade(
    source: str, target: str
) -> None:
    from api.safe_http import headers_for_hop

    headers = {"Authorization": "Bearer x", "Cookie": "s=1"}

    assert headers_for_hop(headers, source, target) == headers


def test_too_many_redirects_is_an_error(
    load_app: Callable[..., ModuleType], serve: Callable[..., Server]
) -> None:
    load_app()
    from api.safe_http import MAX_REDIRECTS, open_public_stream

    server = serve({})
    location = {"Location": server.base_url + "/x"}
    server.routes["/x"] = Route(status=302, headers=location)

    with pytest.raises(requests.TooManyRedirects):
        open_public_stream("GET", server.base_url + "/x", {}, 5)

    assert len(server.hits) == MAX_REDIRECTS + 1
