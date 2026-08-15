import json

import pytest

from megaloader.exceptions import ExtractionError
from megaloader.item import DownloadItem
from megaloader.plugins.pixiv import Pixiv

from tests.helpers import assert_valid_item, fake_fetcher


ARTWORK_ID = "123"
ARTWORK_PAGE = f"https://www.pixiv.net/en/artworks/{ARTWORK_ID}"
PAGES_URL = f"https://www.pixiv.net/ajax/illust/{ARTWORK_ID}/pages"
ILLUST_URL = f"https://www.pixiv.net/ajax/illust/{ARTWORK_ID}"
USER_ID = "42"
USER_PAGE = f"https://www.pixiv.net/users/{USER_ID}"
USER_URL = f"https://www.pixiv.net/ajax/user/{USER_ID}"
USER_WORKS_URL = f"https://www.pixiv.net/ajax/user/{USER_ID}/profile/all"


def _body(body: object, *, error: bool = False, message: str = "") -> str:
    return json.dumps({"error": error, "message": message, "body": body})


def _pages(*urls: str) -> str:
    return _body([{"urls": {"original": url}} for url in urls])


def _extract(url: str, routes: dict[str, str]) -> list[DownloadItem]:
    return list(Pixiv(url).extract(fake_fetcher(routes)))


@pytest.mark.unit
def test_a_multi_page_artwork_yields_every_page_with_a_referer() -> None:
    routes = {
        PAGES_URL: _pages(
            "https://i.pximg.net/img/123_p0.png",
            "https://i.pximg.net/img/123_p1.jpg",
        ),
        ILLUST_URL: _body({"userName": "artist"}),
    }

    items = _extract(ARTWORK_PAGE, routes)

    for item in items:
        assert_valid_item(item)
    assert [item.filename for item in items] == ["123_p0.png", "123_p1.jpg"]
    assert {item.collection_name for item in items} == {"artist_123"}
    # i.pximg.net serves 403 to requests that arrive without a Pixiv referer.
    assert items[0].headers == {
        "Referer": f"https://www.pixiv.net/artworks/{ARTWORK_ID}"
    }


@pytest.mark.unit
def test_an_artwork_the_pages_endpoint_reports_as_empty_is_still_downloadable() -> None:
    # Pixiv answers with an empty page list for some artworks even though the
    # artwork itself has an original image.
    routes = {
        PAGES_URL: _body([]),
        ILLUST_URL: _body(
            {
                "userName": "artist",
                "urls": {"original": "https://i.pximg.net/img/123_p0.png"},
            }
        ),
    }

    items = _extract(ARTWORK_PAGE, routes)

    assert [item.download_url for item in items] == [
        "https://i.pximg.net/img/123_p0.png"
    ]
    assert items[0].collection_name == "artist_123"


@pytest.mark.unit
def test_an_artwork_with_no_original_image_anywhere_yields_nothing() -> None:
    routes = {
        PAGES_URL: _body([]),
        ILLUST_URL: _body({"userName": "artist", "urls": {}}),
    }

    assert _extract(ARTWORK_PAGE, routes) == []


@pytest.mark.unit
def test_pages_missing_an_original_image_are_skipped_without_losing_the_rest() -> None:
    routes = {
        PAGES_URL: _body(
            [{"urls": {}}, {"urls": {"original": "https://i.pximg.net/b.png"}}]
        ),
        ILLUST_URL: _body({"userName": "artist"}),
    }

    items = _extract(ARTWORK_PAGE, routes)

    # Filenames number the pages of the artwork, not the yielded items.
    assert [item.filename for item in items] == ["123_p1.png"]


@pytest.mark.unit
def test_a_rejected_request_surfaces_the_reason_pixiv_gave() -> None:
    routes = {PAGES_URL: _body(None, error=True, message="rate limited")}

    with pytest.raises(ExtractionError) as exc_info:
        _extract(ARTWORK_PAGE, routes)

    err = exc_info.value
    assert err.detail == "rate limited"
    assert err.source == "pixiv"
    assert err.url == PAGES_URL


@pytest.mark.unit
def test_a_rejected_request_without_a_reason_still_fails_loudly() -> None:
    routes = {PAGES_URL: json.dumps({"error": True, "body": None})}

    with pytest.raises(ExtractionError, match="Pixiv API returned an error"):
        _extract(ARTWORK_PAGE, routes)


@pytest.mark.unit
def test_a_user_gallery_yields_profile_art_and_every_work() -> None:
    routes = {
        USER_URL: _body(
            {
                "name": "artist",
                "imageBig": "https://i.pximg.net/user/avatar.jpg",
                "background": {"url": "https://i.pximg.net/user/cover.png"},
            }
        ),
        USER_WORKS_URL: _body({"illusts": {"123": None}, "manga": {"456": None}}),
        PAGES_URL: _pages("https://i.pximg.net/img/123_p0.png"),
        "https://www.pixiv.net/ajax/illust/456/pages": _pages(
            "https://i.pximg.net/img/456_p0.png"
        ),
    }

    items = _extract(USER_PAGE, routes)

    assert [item.filename for item in items] == [
        "avatar.jpg",
        "cover.png",
        "123_p0.png",
        "456_p0.png",
    ]
    # Everything a gallery discovers lands in one folder named after the user,
    # including manga, rather than one folder per artwork.
    assert {item.collection_name for item in items} == {"42_artist"}


@pytest.mark.unit
def test_a_gallery_pixiv_refuses_to_describe_yields_nothing() -> None:
    assert _extract(USER_PAGE, {USER_URL: _body(None)}) == []


@pytest.mark.unit
def test_a_gallery_without_profile_art_or_works_yields_nothing() -> None:
    routes = {
        USER_URL: _body({"name": "artist", "background": None}),
        USER_WORKS_URL: _body(None),
    }

    assert _extract(USER_PAGE, routes) == []


@pytest.mark.unit
def test_requests_are_anonymous_unless_a_session_id_is_available(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("PIXIV_PHPSESSID", raising=False)

    config = Pixiv(USER_PAGE).session_config()

    assert config.headers == {"Referer": "https://www.pixiv.net/"}
    assert config.cookies == ()


@pytest.mark.unit
@pytest.mark.parametrize(
    ("options", "expected"),
    [
        pytest.param({}, "from-env", id="environment"),
        pytest.param({"session_id": "explicit"}, "explicit", id="explicit-wins"),
    ],
)
def test_a_session_id_authenticates_requests_for_restricted_art(
    monkeypatch: pytest.MonkeyPatch, options: dict[str, str], expected: str
) -> None:
    monkeypatch.setenv("PIXIV_PHPSESSID", "from-env")

    config = Pixiv(USER_PAGE, **options).session_config()

    assert [(c.name, c.value, c.domain) for c in config.cookies] == [
        ("PHPSESSID", expected, ".pixiv.net")
    ]
