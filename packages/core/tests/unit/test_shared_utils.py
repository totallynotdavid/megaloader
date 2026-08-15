from collections.abc import Generator

import pytest

from megaloader.exceptions import ExtractionError
from megaloader.fetcher import Fetcher, Request, Response
from megaloader.item import DownloadItem, items_from_pairs
from megaloader.pagination import crawl_pages
from megaloader.parsing import absolute_links, element_text, parse_html, unique
from megaloader.plugin import BasePlugin


def _response(text: str, url: str = "https://example.com/") -> Response:
    return Response(url=url, status_code=200, text=text, content=text.encode())


def _fetcher(pages: dict[str, str]) -> Fetcher:
    def fetch(request: Request) -> Response:
        page = str(dict(request.params or {}).get("page", request.url))
        if page not in pages:
            msg = "missing page"
            raise ExtractionError(msg, url=request.url, http_status=404)
        return _response(pages[page], request.url)

    return fetch


@pytest.mark.unit
def test_unique_preserves_first_occurrence_order() -> None:
    assert list(unique(["b", "a", "b", "c", "a"])) == ["b", "a", "c"]


@pytest.mark.unit
def test_element_text_strips_and_falls_back() -> None:
    soup = parse_html("<h1>  Album title\n</h1>")

    assert element_text(soup.find("h1"), "album") == "Album title"
    assert element_text(soup.find("h2"), "album") == "album"
    assert element_text(soup.find("h2")) is None


@pytest.mark.unit
def test_absolute_links_resolves_and_dedupes() -> None:
    soup = parse_html(
        '<a class="file" href="/f/one"></a>'
        '<a class="file" href="/f/one"></a>'
        '<a class="file" href="/f/two"></a>'
        '<a class="other" href="/f/three"></a>'
    )

    assert absolute_links(soup, "a.file[href]", "https://example.com/album") == [
        "https://example.com/f/one",
        "https://example.com/f/two",
    ]


@pytest.mark.unit
def test_items_from_pairs_shares_collection() -> None:
    items = list(
        items_from_pairs(
            [("https://example.com/a.jpg", "a.jpg")], collection_name="album"
        )
    )

    assert [
        (item.download_url, item.filename, item.collection_name) for item in items
    ] == [("https://example.com/a.jpg", "a.jpg", "album")]


@pytest.mark.unit
def test_crawl_pages_walks_until_empty_body() -> None:
    fetch = _fetcher({"1": "first", "2": "second", "3": "  "})

    pages = [response.text for response in crawl_pages(fetch, _page_request)]

    assert pages == ["first", "second"]


@pytest.mark.unit
def test_crawl_pages_honors_start_and_step() -> None:
    fetch = _fetcher({"0": "first", "42": "second", "84": ""})

    pages = [
        response.text
        for response in crawl_pages(fetch, _page_request, start=0, step=42)
    ]

    assert pages == ["first", "second"]


@pytest.mark.unit
def test_crawl_pages_stops_on_declared_status() -> None:
    fetch = _fetcher({"1": "first"})

    pages = [
        response.text
        for response in crawl_pages(fetch, _page_request, stop_statuses=(404,))
    ]

    assert pages == ["first"]


@pytest.mark.unit
def test_crawl_pages_reraises_undeclared_status() -> None:
    fetch = _fetcher({"1": "first"})

    with pytest.raises(ExtractionError):
        list(crawl_pages(fetch, _page_request))


def _page_request(page: int) -> Request:
    return Request("https://example.com/list", params={"page": page})


class _DummyPlugin(BasePlugin):
    def extract(self, fetch: Fetcher) -> Generator[DownloadItem, None, None]:
        raise NotImplementedError


@pytest.mark.unit
def test_option_prefers_kwarg_over_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DUMMY_TOKEN", "from-env")
    plugin = _DummyPlugin("https://example.com/", token="from-kwarg")

    assert plugin.option("token", env="DUMMY_TOKEN") == "from-kwarg"


@pytest.mark.unit
def test_option_falls_back_to_environment_then_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DUMMY_TOKEN", "from-env")
    plugin = _DummyPlugin("https://example.com/")

    assert plugin.option("token", env="DUMMY_TOKEN") == "from-env"

    monkeypatch.delenv("DUMMY_TOKEN")
    assert plugin.option("token", env="DUMMY_TOKEN") is None
    assert plugin.option("token") is None
