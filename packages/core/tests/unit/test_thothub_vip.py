import json

import pytest

from megaloader.exceptions import ExtractionError
from megaloader.plugins.thothub_vip import (
    ThothubVIP,
    parse_album,
    parse_model_links,
    parse_video_metadata,
)

from tests.helpers import fake_fetcher


MODEL_URL = "https://thothub.vip/models/foo/"
VIDEO_URL = "https://thothub.vip/video/1/clip/"
ALBUM_URL = "https://thothub.vip/album/2/set/"


def _video_page(name: str = "Clip", content_url: str | None = "/cdn/clip.mp4") -> str:
    metadata: dict[str, str] = {"name": name}
    if content_url is not None:
        metadata["contentUrl"] = content_url
    return f'<script type="application/ld+json">{json.dumps(metadata)}</script>'


def _album_page(*hrefs: str) -> str:
    links = "".join(f'<a class="item album-img" href="{href}"></a>' for href in hrefs)
    return f'<h1 class="title">Set</h1><div class="album-inner">{links}</div>'


@pytest.mark.unit
def test_parse_model_links_dedupes_and_keeps_document_order() -> None:
    page = (
        '<div class="title">Foo</div>'
        f'<a href="{VIDEO_URL}"></a>'
        '<a href="/video/1/clip/"></a>'
        '<a href="/video/3/other/"></a>'
        f'<a href="{ALBUM_URL}"></a>'
        '<a href="/album/2/set/"></a>'
        '<a href="/tags/bar/"></a>'
    )

    model_name, video_urls, album_urls = parse_model_links(page, MODEL_URL)

    assert model_name == "Foo"
    assert video_urls == [VIDEO_URL, "https://thothub.vip/video/3/other/"]
    assert album_urls == [ALBUM_URL]


@pytest.mark.unit
def test_parse_model_links_returns_none_name_without_title() -> None:
    model_name, video_urls, album_urls = parse_model_links("<div></div>", MODEL_URL)

    assert model_name is None
    assert video_urls == []
    assert album_urls == []


@pytest.mark.unit
def test_parse_video_metadata_reads_ld_json() -> None:
    content_url, title = parse_video_metadata(_video_page(), VIDEO_URL)

    assert content_url == "/cdn/clip.mp4"
    assert title == "Clip"


@pytest.mark.unit
def test_parse_video_metadata_defaults_title_when_absent() -> None:
    page = '<script type="application/ld+json">{"contentUrl": "/a.mp4"}</script>'

    assert parse_video_metadata(page, VIDEO_URL) == ("/a.mp4", "video")


@pytest.mark.unit
def test_parse_video_metadata_requires_ld_json_block() -> None:
    with pytest.raises(ExtractionError) as exc_info:
        parse_video_metadata("<html></html>", VIDEO_URL)

    err = exc_info.value
    assert err.category == "protocol"
    assert err.source == "thothubvip"
    assert err.url == VIDEO_URL


@pytest.mark.unit
def test_parse_video_metadata_requires_content_url() -> None:
    with pytest.raises(ExtractionError, match="No contentUrl"):
        parse_video_metadata(_video_page(content_url=None), VIDEO_URL)


@pytest.mark.unit
def test_parse_album_resolves_relative_hrefs_and_skips_nameless_ones() -> None:
    page = _album_page("/media/a.jpg", "https://cdn.thothub.vip/b.png", "/")

    collection_name, files = parse_album(page, ALBUM_URL)

    assert collection_name == "Set"
    assert files == [
        ("https://thothub.vip/media/a.jpg", "a.jpg"),
        ("https://cdn.thothub.vip/b.png", "b.png"),
    ]


@pytest.mark.unit
def test_parse_album_falls_back_to_generic_collection_name() -> None:
    collection_name, files = parse_album('<div class="album-inner"></div>', ALBUM_URL)

    assert collection_name == "album"
    assert files == []


@pytest.mark.unit
def test_extract_video_target_yields_absolute_download_url() -> None:
    routes = {VIDEO_URL: _video_page()}

    items = list(ThothubVIP(VIDEO_URL).extract(fake_fetcher(routes)))

    assert len(items) == 1
    assert items[0].download_url == "https://thothub.vip/cdn/clip.mp4"
    assert items[0].filename == "Clip.mp4"
    assert items[0].collection_name is None


@pytest.mark.unit
def test_extract_album_target_yields_every_file() -> None:
    routes = {ALBUM_URL: _album_page("/media/a.jpg", "/media/b.png")}

    items = list(ThothubVIP(ALBUM_URL).extract(fake_fetcher(routes)))

    assert [item.filename for item in items] == ["a.jpg", "b.png"]
    assert {item.collection_name for item in items} == {"Set"}


@pytest.mark.unit
def test_extract_model_target_walks_videos_then_albums() -> None:
    model_page = (
        '<div class="title">Foo</div>'
        f'<a href="{VIDEO_URL}"></a>'
        f'<a href="{ALBUM_URL}"></a>'
    )
    routes = {
        MODEL_URL: model_page,
        VIDEO_URL: _video_page(),
        ALBUM_URL: _album_page("/media/a.jpg"),
    }

    items = list(ThothubVIP(MODEL_URL).extract(fake_fetcher(routes)))

    assert [item.filename for item in items] == ["Clip.mp4", "a.jpg"]
    # The video inherits the model name; album files keep their own album title.
    assert [item.collection_name for item in items] == ["Foo", "Set"]


@pytest.mark.unit
def test_extract_unsupported_url_yields_nothing() -> None:
    routes: dict[str, str] = {}

    items = list(
        ThothubVIP("https://thothub.vip/unknown").extract(fake_fetcher(routes))
    )

    assert items == []
