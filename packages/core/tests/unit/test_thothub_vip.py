import json

import pytest

from megaloader.exceptions import ExtractionError
from megaloader.item import DownloadItem
from megaloader.plugins.thothub_vip import ThothubVIP

from tests.helpers import assert_valid_item, fake_fetcher


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


def _extract(url: str, routes: dict[str, str]) -> list[DownloadItem]:
    return list(ThothubVIP(url).extract(fake_fetcher(routes)))


@pytest.mark.unit
def test_a_video_page_yields_one_downloadable_file() -> None:
    items = _extract(VIDEO_URL, {VIDEO_URL: _video_page()})

    assert len(items) == 1
    assert_valid_item(items[0])
    # The site advertises the media as a site-relative path.
    assert items[0].download_url == "https://thothub.vip/cdn/clip.mp4"
    assert items[0].filename == "Clip.mp4"


@pytest.mark.unit
def test_an_untitled_video_still_gets_a_filename() -> None:
    page = '<script type="application/ld+json">{"contentUrl": "/a.mp4"}</script>'

    items = _extract(VIDEO_URL, {VIDEO_URL: page})

    assert [item.filename for item in items] == ["video.mp4"]


@pytest.mark.unit
@pytest.mark.parametrize(
    "page",
    [
        pytest.param("<html></html>", id="no-metadata-block"),
        pytest.param(_video_page(content_url=None), id="metadata-without-media-url"),
    ],
)
def test_a_video_page_without_usable_metadata_fails_loudly(page: str) -> None:
    # Silently yielding nothing would look like an empty video to callers, so
    # the plugin reports an unusable page as an extraction failure instead.
    with pytest.raises(ExtractionError) as exc_info:
        _extract(VIDEO_URL, {VIDEO_URL: page})

    assert exc_info.value.url == VIDEO_URL


@pytest.mark.unit
def test_an_album_yields_every_image_and_skips_nameless_urls() -> None:
    page = _album_page("/media/a.jpg", "https://cdn.thothub.vip/b.png", "/")

    items = _extract(ALBUM_URL, {ALBUM_URL: page})

    for item in items:
        assert_valid_item(item)
    assert [item.download_url for item in items] == [
        "https://thothub.vip/media/a.jpg",
        "https://cdn.thothub.vip/b.png",
    ]
    assert {item.collection_name for item in items} == {"Set"}


@pytest.mark.unit
def test_an_untitled_album_still_groups_its_images() -> None:
    page = '<div class="album-inner"><a class="item album-img" href="/a.jpg"></a></div>'

    items = _extract(ALBUM_URL, {ALBUM_URL: page})

    assert [item.collection_name for item in items] == ["album"]


@pytest.mark.unit
def test_a_model_yields_its_videos_then_its_albums_once_each() -> None:
    # Model pages link the same video from a thumbnail grid and a sidebar, both
    # as absolute and site-relative hrefs.
    model_page = (
        '<div class="title">Foo</div>'
        f'<a href="{VIDEO_URL}"></a>'
        '<a href="/video/1/clip/"></a>'
        f'<a href="{ALBUM_URL}"></a>'
        '<a href="/album/2/set/"></a>'
        '<a href="/tags/bar/"></a>'
    )
    routes = {
        MODEL_URL: model_page,
        VIDEO_URL: _video_page(),
        ALBUM_URL: _album_page("/media/a.jpg"),
    }

    items = _extract(MODEL_URL, routes)

    assert [item.filename for item in items] == ["Clip.mp4", "a.jpg"]
    # Videos are grouped under the model; album images keep their album title.
    assert [item.collection_name for item in items] == ["Foo", "Set"]


@pytest.mark.unit
def test_a_url_that_is_neither_model_video_nor_album_yields_nothing() -> None:
    assert _extract("https://thothub.vip/unknown", {}) == []
