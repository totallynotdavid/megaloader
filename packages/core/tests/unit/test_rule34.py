from collections.abc import Mapping

import pytest

from bs4 import BeautifulSoup
from megaloader.fetcher import Fetcher, Request, Response
from megaloader.plugins.rule34 import (
    Rule34,
    build_item,
    parse_listing_hrefs,
    parse_media_url,
    parse_query,
)


API_URL = "https://api.rule34.xxx/index.php"
LISTING_URL = "https://rule34.xxx/index.php"


def paging_fetcher(
    pages: Mapping[str, list[str]], routes: Mapping[str, str] | None = None
) -> Fetcher:
    """Serve a different body per request to the same paginated URL.

    Rule34 drives pagination through query parameters on one endpoint, so the
    URL alone cannot identify a page: each entry in pages is consumed in order,
    and exhausting it emits an empty body, which is how the real endpoint
    signals the end of a listing.
    """
    remaining = {url: list(bodies) for url, bodies in pages.items()}

    def fetch(request: Request) -> Response:
        queue = remaining.get(request.url)
        if queue is not None:
            body = queue.pop(0) if queue else ""
        elif routes and request.url in routes:
            body = routes[request.url]
        else:
            msg = f"unexpected request to {request.url}"
            raise AssertionError(msg)

        return Response(
            url=request.url, status_code=200, text=body, content=body.encode()
        )

    return fetch


def _post_page(media_url: str) -> str:
    return f'<a href="{media_url}">Original image</a>'


def _api_page(*posts: tuple[str, str]) -> str:
    entries = "".join(
        f'<post id="{post_id}" file_url="{file_url}"/>' for post_id, file_url in posts
    )
    return f"<posts>{entries}</posts>"


def _listing_page(*hrefs: str) -> str:
    thumbs = "".join(
        f'<span class="thumb"><a href="{href}"></a></span>' for href in hrefs
    )
    return f'<div class="image-list">{thumbs}</div>'


@pytest.mark.unit
def test_parse_query_reads_post_id_and_tags() -> None:
    assert parse_query("https://rule34.xxx/index.php?page=post&s=view&id=99") == (
        "99",
        [],
    )
    assert parse_query("https://rule34.xxx/index.php?tags=cat+dog") == (
        None,
        ["cat", "dog"],
    )


@pytest.mark.unit
def test_constructor_rejects_url_without_id_or_tags() -> None:
    with pytest.raises(ValueError, match="'id' or 'tags'"):
        Rule34("https://rule34.xxx/index.php?page=post&s=list")


@pytest.mark.unit
@pytest.mark.parametrize(
    ("html", "expected"),
    [
        (
            '<a href="https://img.rule34.xxx/a.jpg">Original image</a>',
            "https://img.rule34.xxx/a.jpg",
        ),
        (
            '<video><source src="https://img.rule34.xxx/a.mp4"></video>',
            "https://img.rule34.xxx/a.mp4",
        ),
        (
            '<img id="image" src="https://img.rule34.xxx/a.png">',
            "https://img.rule34.xxx/a.png",
        ),
        ("<div>no media here</div>", None),
    ],
)
def test_parse_media_url_covers_each_post_layout(
    html: str, expected: str | None
) -> None:
    assert parse_media_url(BeautifulSoup(html, "html.parser")) == expected


@pytest.mark.unit
def test_parse_listing_hrefs_returns_thumbnail_links() -> None:
    soup = BeautifulSoup(
        _listing_page("index.php?id=1", "index.php?id=2"), "html.parser"
    )

    assert parse_listing_hrefs(soup) == ["index.php?id=1", "index.php?id=2"]


@pytest.mark.unit
def test_build_item_upgrades_protocol_relative_urls() -> None:
    item = build_item("//img.rule34.xxx/images/a.jpg", "cats", "7")

    assert item.download_url == "https://img.rule34.xxx/images/a.jpg"
    assert item.filename == "a.jpg"
    assert item.collection_name == "cats"
    assert item.source_id == "7"


@pytest.mark.unit
def test_single_post_extraction_yields_one_item() -> None:
    post_url = "https://rule34.xxx/index.php?page=post&s=view&id=99"
    fetch = paging_fetcher({}, {post_url: _post_page("//img.rule34.xxx/a.jpg")})

    items = list(Rule34(post_url).extract(fetch))

    assert len(items) == 1
    assert items[0].source_id == "99"
    assert items[0].collection_name == "post_99"


@pytest.mark.unit
def test_single_post_without_media_yields_nothing() -> None:
    post_url = "https://rule34.xxx/index.php?page=post&s=view&id=99"
    fetch = paging_fetcher({}, {post_url: "<div></div>"})

    assert list(Rule34(post_url).extract(fetch)) == []


@pytest.mark.unit
def test_api_extraction_pages_until_an_empty_response() -> None:
    fetch = paging_fetcher(
        {
            API_URL: [
                _api_page(("1", "https://img.rule34.xxx/a.jpg")),
                _api_page(("2", "https://img.rule34.xxx/b.png")),
                _api_page(),
            ]
        }
    )

    plugin = Rule34(
        "https://rule34.xxx/index.php?tags=dog+cat", api_key="key", user_id="uid"
    )
    items = list(plugin.extract(fetch))

    assert [item.source_id for item in items] == ["1", "2"]
    # Tags are sorted so the same query always lands in the same collection.
    assert {item.collection_name for item in items} == {"cat_dog"}


@pytest.mark.unit
def test_api_extraction_skips_posts_without_a_file_url() -> None:
    fetch = paging_fetcher(
        {
            API_URL: [
                '<posts><post id="1"/><post id="2" file_url="//img/b.png"/></posts>',
                "",
            ]
        }
    )

    plugin = Rule34(
        "https://rule34.xxx/index.php?tags=cat", api_key="key", user_id="uid"
    )

    assert [item.source_id for item in plugin.extract(fetch)] == ["2"]


@pytest.mark.unit
def test_api_extraction_stops_when_the_body_is_not_xml() -> None:
    # Rate limits and outages answer with plain text; the loop must end instead
    # of paging forever against an endpoint that never returns posts.
    fetch = paging_fetcher({API_URL: ["503 Service Temporarily Unavailable"]})

    plugin = Rule34(
        "https://rule34.xxx/index.php?tags=cat", api_key="key", user_id="uid"
    )

    assert list(plugin.extract(fetch)) == []


@pytest.mark.unit
def test_scraper_extraction_dedupes_posts_across_pages(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("RULE34_API_KEY", raising=False)
    monkeypatch.delenv("RULE34_USER_ID", raising=False)

    first = "index.php?page=post&s=view&id=1"
    second = "index.php?page=post&s=view&id=2"
    fetch = paging_fetcher(
        {LISTING_URL: [_listing_page(first, second), _listing_page(first), ""]},
        {
            f"https://rule34.xxx/{first}": _post_page("//img.rule34.xxx/a.jpg"),
            f"https://rule34.xxx/{second}": _post_page("//img.rule34.xxx/b.png"),
        },
    )

    items = list(Rule34("https://rule34.xxx/index.php?tags=cat").extract(fetch))

    assert [item.filename for item in items] == ["a.jpg", "b.png"]


@pytest.mark.unit
def test_scraper_extraction_falls_back_when_credentials_are_partial(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("RULE34_USER_ID", raising=False)
    fetch = paging_fetcher({LISTING_URL: [""]})

    plugin = Rule34("https://rule34.xxx/index.php?tags=cat", api_key="key")

    assert list(plugin.extract(fetch)) == []
