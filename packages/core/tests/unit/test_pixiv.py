import json

import pytest

from megaloader.exceptions import ExtractionError
from megaloader.plugins.pixiv import Pixiv

from tests.helpers import fake_fetcher


ARTWORK_ID = "123"
PAGES_URL = f"https://www.pixiv.net/ajax/illust/{ARTWORK_ID}/pages"
ILLUST_URL = f"https://www.pixiv.net/ajax/illust/{ARTWORK_ID}"
USER_ID = "42"
USER_URL = f"https://www.pixiv.net/ajax/user/{USER_ID}"
USER_WORKS_URL = f"https://www.pixiv.net/ajax/user/{USER_ID}/profile/all"


def _body(body: object, *, error: bool = False, message: str = "") -> str:
    return json.dumps({"error": error, "message": message, "body": body})


def _pages(*urls: str) -> str:
    return _body([{"urls": {"original": url}} for url in urls])


@pytest.mark.unit
def test_artwork_yields_one_item_per_page() -> None:
    routes = {
        PAGES_URL: _pages(
            "https://i.pximg.net/img/123_p0.png",
            "https://i.pximg.net/img/123_p1.jpg",
        ),
        ILLUST_URL: _body({"userName": "artist"}),
    }

    items = list(
        Pixiv(f"https://www.pixiv.net/en/artworks/{ARTWORK_ID}").extract(
            fake_fetcher(routes)
        )
    )

    assert [item.filename for item in items] == ["123_p0.png", "123_p1.jpg"]
    assert {item.collection_name for item in items} == {"artist_123"}
    assert items[0].headers == {
        "Referer": f"https://www.pixiv.net/artworks/{ARTWORK_ID}"
    }


@pytest.mark.unit
def test_artwork_falls_back_to_illust_detail_when_pages_is_empty() -> None:
    # The pages endpoint returns an empty list for some artworks; the single
    # original URL then has to come from the illust detail payload, which is
    # also reused for the collection name instead of being fetched twice.
    routes = {
        PAGES_URL: _body([]),
        ILLUST_URL: _body(
            {
                "userName": "artist",
                "urls": {"original": "https://i.pximg.net/img/123_p0.png"},
            }
        ),
    }

    items = list(
        Pixiv(f"https://www.pixiv.net/en/artworks/{ARTWORK_ID}").extract(
            fake_fetcher(routes)
        )
    )

    assert len(items) == 1
    assert items[0].download_url == "https://i.pximg.net/img/123_p0.png"
    assert items[0].collection_name == "artist_123"


@pytest.mark.unit
def test_artwork_without_any_original_url_yields_nothing() -> None:
    routes = {
        PAGES_URL: _body([]),
        ILLUST_URL: _body({"userName": "artist", "urls": {}}),
    }

    items = list(
        Pixiv(f"https://www.pixiv.net/en/artworks/{ARTWORK_ID}").extract(
            fake_fetcher(routes)
        )
    )

    assert items == []


@pytest.mark.unit
def test_artwork_skips_pages_without_an_original_url() -> None:
    routes = {
        PAGES_URL: json.dumps(
            {
                "error": False,
                "body": [
                    {"urls": {}},
                    {"urls": {"original": "https://i.pximg.net/b.png"}},
                ],
            }
        ),
        ILLUST_URL: _body({"userName": "artist"}),
    }

    items = list(
        Pixiv(f"https://www.pixiv.net/en/artworks/{ARTWORK_ID}").extract(
            fake_fetcher(routes)
        )
    )

    assert [item.filename for item in items] == ["123_p1.png"]


@pytest.mark.unit
def test_api_error_flag_raises_extraction_error() -> None:
    routes = {PAGES_URL: _body(None, error=True, message="rate limited")}

    with pytest.raises(ExtractionError) as exc_info:
        list(
            Pixiv(f"https://www.pixiv.net/en/artworks/{ARTWORK_ID}").extract(
                fake_fetcher(routes)
            )
        )

    err = exc_info.value
    assert err.detail == "rate limited"
    assert err.source == "pixiv"
    assert err.url == PAGES_URL
    assert err.provider_status == "True"


@pytest.mark.unit
def test_api_error_without_message_uses_generic_detail() -> None:
    routes = {PAGES_URL: json.dumps({"error": True, "body": None})}

    with pytest.raises(ExtractionError, match="Pixiv API returned an error"):
        list(
            Pixiv(f"https://www.pixiv.net/en/artworks/{ARTWORK_ID}").extract(
                fake_fetcher(routes)
            )
        )


@pytest.mark.unit
def test_user_gallery_yields_avatar_cover_and_every_work() -> None:
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

    items = list(
        Pixiv(f"https://www.pixiv.net/users/{USER_ID}").extract(fake_fetcher(routes))
    )

    assert [item.filename for item in items] == [
        "avatar.jpg",
        "cover.png",
        "123_p0.png",
        "456_p0.png",
    ]
    # Works discovered through a gallery inherit the gallery's collection name
    # rather than deriving a per-artwork one, so they land in a single folder.
    assert {item.collection_name for item in items} == {"42_artist"}


@pytest.mark.unit
def test_user_gallery_without_profile_body_yields_nothing() -> None:
    routes = {USER_URL: _body(None)}

    items = list(
        Pixiv(f"https://www.pixiv.net/users/{USER_ID}").extract(fake_fetcher(routes))
    )

    assert items == []


@pytest.mark.unit
def test_user_gallery_tolerates_missing_avatar_cover_and_works() -> None:
    routes = {
        USER_URL: _body({"name": "artist", "background": None}),
        USER_WORKS_URL: _body(None),
    }

    items = list(
        Pixiv(f"https://www.pixiv.net/users/{USER_ID}").extract(fake_fetcher(routes))
    )

    assert items == []


@pytest.mark.unit
def test_session_config_sends_referer_without_cookies_by_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("PIXIV_PHPSESSID", raising=False)

    config = Pixiv(f"https://www.pixiv.net/users/{USER_ID}").session_config()

    assert config.headers == {"Referer": "https://www.pixiv.net/"}
    assert config.cookies == ()


@pytest.mark.unit
def test_session_config_prefers_explicit_session_id_over_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PIXIV_PHPSESSID", "from-env")

    config = Pixiv(
        f"https://www.pixiv.net/users/{USER_ID}", session_id="explicit"
    ).session_config()

    assert len(config.cookies) == 1
    cookie = config.cookies[0]
    assert (cookie.name, cookie.value, cookie.domain) == (
        "PHPSESSID",
        "explicit",
        ".pixiv.net",
    )


@pytest.mark.unit
def test_session_config_falls_back_to_environment_session_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PIXIV_PHPSESSID", "from-env")

    config = Pixiv(f"https://www.pixiv.net/users/{USER_ID}").session_config()

    assert [cookie.value for cookie in config.cookies] == ["from-env"]
