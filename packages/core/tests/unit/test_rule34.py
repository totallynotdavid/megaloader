from collections.abc import Mapping

import pytest

from megaloader.fetcher import Fetcher, Request, Response
from megaloader.plugins.rule34 import Rule34

from tests.helpers import assert_valid_item


API_URL = "https://api.rule34.xxx/index.php"
LISTING_URL = "https://rule34.xxx/index.php"
POST_URL = "https://rule34.xxx/index.php?page=post&s=view&id=99"


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
def test_a_url_that_names_neither_a_post_nor_tags_is_rejected() -> None:
    with pytest.raises(ValueError, match="'id' or 'tags'"):
        Rule34("https://rule34.xxx/index.php?page=post&s=list")


@pytest.mark.unit
@pytest.mark.parametrize(
    ("page", "expected_url"),
    [
        pytest.param(
            '<a href="//img.rule34.xxx/a.jpg">Original image</a>',
            "https://img.rule34.xxx/a.jpg",
            id="original-image-link",
        ),
        pytest.param(
            '<video><source src="//img.rule34.xxx/a.mp4"></video>',
            "https://img.rule34.xxx/a.mp4",
            id="video-post",
        ),
        pytest.param(
            '<img id="image" src="//img.rule34.xxx/a.png">',
            "https://img.rule34.xxx/a.png",
            id="plain-image-post",
        ),
    ],
)
def test_a_single_post_yields_its_media_whatever_the_page_layout(
    page: str, expected_url: str
) -> None:
    items = list(Rule34(POST_URL).extract(paging_fetcher({}, {POST_URL: page})))

    assert len(items) == 1
    assert_valid_item(items[0])
    # Rule34 serves protocol-relative media URLs, which are not downloadable.
    assert items[0].download_url == expected_url
    assert items[0].source_id == "99"
    assert items[0].collection_name == "post_99"


@pytest.mark.unit
def test_a_post_carrying_no_media_yields_nothing() -> None:
    fetch = paging_fetcher({}, {POST_URL: "<div></div>"})

    assert list(Rule34(POST_URL).extract(fetch)) == []


@pytest.mark.unit
def test_a_tag_query_pages_through_the_api_until_it_runs_out_of_posts() -> None:
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
def test_posts_the_api_reports_without_a_file_are_left_out() -> None:
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
def test_an_api_outage_ends_the_extraction_instead_of_paging_forever() -> None:
    # Rate limits and outages answer with plain text rather than XML.
    fetch = paging_fetcher({API_URL: ["503 Service Temporarily Unavailable"]})

    plugin = Rule34(
        "https://rule34.xxx/index.php?tags=cat", api_key="key", user_id="uid"
    )

    assert list(plugin.extract(fetch)) == []


@pytest.mark.unit
def test_a_tag_query_without_api_credentials_scrapes_each_post_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Listings repeat posts across pages as new uploads shift the ordering.
    monkeypatch.delenv("RULE34_API_KEY", raising=False)
    monkeypatch.delenv("RULE34_USER_ID", raising=False)

    first = "index.php?page=post&s=view&id=1"
    second = "index.php?page=post&s=view&id=2"
    fetch = paging_fetcher(
        {LISTING_URL: [_listing_page(first, second), _listing_page(first), ""]},
        {
            f"https://rule34.xxx/{first}": '<a href="//img.rule34.xxx/a.jpg">'
            "Original image</a>",
            f"https://rule34.xxx/{second}": '<a href="//img.rule34.xxx/b.png">'
            "Original image</a>",
        },
    )

    items = list(Rule34("https://rule34.xxx/index.php?tags=cat").extract(fetch))

    assert [item.filename for item in items] == ["a.jpg", "b.png"]


@pytest.mark.unit
def test_half_a_credential_pair_still_takes_the_scraping_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # The API rejects a key without a user id, so anything short of both
    # credentials must fall back to scraping: only the listing is served here,
    # and a request to the API endpoint would fail the test.
    monkeypatch.delenv("RULE34_USER_ID", raising=False)
    fetch = paging_fetcher({LISTING_URL: [""]})

    plugin = Rule34("https://rule34.xxx/index.php?tags=cat", api_key="key")

    assert list(plugin.extract(fetch)) == []
