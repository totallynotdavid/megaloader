"""Failures that used to be swallowed must reach the caller as ExtractionError.

Each case injects a response a site can plausibly return (an HTML error page
where JSON was promised, a truncated blob, a payload missing a field) and
asserts the extraction stops loudly with metadata attached, instead of yielding
nothing and looking like an empty gallery.
"""

import base64

import pytest

from megaloader.exceptions import ExtractionError
from megaloader.fetcher import Response
from megaloader.plugin import BasePlugin
from megaloader.plugins.bunkr import Bunkr, decrypt_direct_url
from megaloader.plugins.cyberdrop import Cyberdrop
from megaloader.plugins.gofile import Gofile
from megaloader.plugins.pixeldrain import PixelDrain
from megaloader.plugins.pixiv import Pixiv
from megaloader.plugins.rule34 import Rule34
from megaloader.plugins.thothub_to import ThothubTO
from megaloader.plugins.thothub_vip import ThothubVIP, parse_video_metadata

from tests.helpers import fake_fetcher


@pytest.mark.unit
def test_non_json_body_becomes_extraction_error() -> None:
    response = Response(
        url="https://api.example.com/v1",
        status_code=200,
        text="<html>Just a moment...</html>",
        content=b"<html>Just a moment...</html>",
        source="bunkr",
    )

    with pytest.raises(ExtractionError) as excinfo:
        response.json()

    error = excinfo.value
    assert error.category == "protocol"
    assert error.source == "bunkr"
    assert error.url == "https://api.example.com/v1"
    assert error.http_status == 200
    assert isinstance(error.cause, ValueError)
    assert isinstance(error.__cause__, ValueError)


@pytest.mark.unit
@pytest.mark.parametrize(
    ("plugin", "url"),
    [
        (Bunkr, "https://bunkr.si/v/something"),
        (Cyberdrop, "https://cyberdrop.me/v/something"),
        (ThothubTO, "https://thothub.to/categories/something/"),
        (ThothubVIP, "https://thothub.vip/categories/something/"),
    ],
)
def test_unsupported_url_shape_raises(plugin: type[BasePlugin], url: str) -> None:
    # A URL the plugin cannot classify is a caller mistake, not an empty result.
    with pytest.raises(ValueError, match="Unrecognized"):
        list(plugin(url).extract(fake_fetcher({})))


@pytest.mark.unit
def test_rule34_api_non_xml_body_raises() -> None:
    # An outage page from the API must not read as "no more pages", which would
    # hand back a silently truncated (here: empty) result set.
    plugin = Rule34(
        "https://rule34.xxx/index.php?page=post&s=list&tags=foo",
        api_key="k",
        user_id="1",
    )
    routes = {"https://api.rule34.xxx/index.php": "maintenance in progress"}

    with pytest.raises(ExtractionError) as excinfo:
        list(plugin.extract(fake_fetcher(routes)))

    assert excinfo.value.category == "protocol"
    assert excinfo.value.source == "rule34"


@pytest.mark.unit
def test_rule34_single_post_without_media_raises() -> None:
    url = "https://rule34.xxx/index.php?page=post&s=view&id=7"
    plugin = Rule34(url)

    with pytest.raises(ExtractionError, match="No media found"):
        list(plugin.extract(fake_fetcher({url: "<html><body>gone</body></html>"})))


@pytest.mark.unit
def test_pixeldrain_malformed_viewer_data_raises() -> None:
    url = "https://pixeldrain.com/l/abc123"
    page = "<script>window.viewer_data = {not valid json};</script>"

    with pytest.raises(ExtractionError) as excinfo:
        list(PixelDrain(url).extract(fake_fetcher({url: page})))

    error = excinfo.value
    assert error.category == "protocol"
    assert error.url == url
    assert isinstance(error.cause, ValueError)


@pytest.mark.unit
def test_pixeldrain_viewer_data_without_files_raises() -> None:
    url = "https://pixeldrain.com/l/abc123"
    page = '<script>window.viewer_data = {"type": "list", "api_response": {}};</script>'

    with pytest.raises(ExtractionError, match="no files"):
        list(PixelDrain(url).extract(fake_fetcher({url: page})))


@pytest.mark.unit
def test_gofile_guest_token_response_without_token_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("GOFILE_TOKEN", raising=False)
    monkeypatch.setattr("megaloader.plugins.gofile._token_cache", {})

    routes = {"https://api.gofile.io/accounts": '{"status": "ok", "data": {}}'}

    with pytest.raises(ExtractionError, match="no token"):
        list(Gofile("https://gofile.io/d/abc123").extract(fake_fetcher(routes)))


@pytest.mark.unit
def test_gofile_file_entry_without_link_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GOFILE_TOKEN", "token")
    contents = (
        '{"status": "ok", "data": {"name": "folder", "children": '
        '{"1": {"type": "file", "id": "1", "name": "clip.mp4"}}}}'
    )
    routes = {"https://api.gofile.io/contents/abc123": contents}

    with pytest.raises(ExtractionError) as excinfo:
        list(Gofile("https://gofile.io/d/abc123").extract(fake_fetcher(routes)))

    assert excinfo.value.category == "protocol"


@pytest.mark.unit
def test_pixiv_requested_artwork_without_image_raises() -> None:
    routes = {
        "https://www.pixiv.net/ajax/illust/123/pages": '{"error": false, "body": []}',
        "https://www.pixiv.net/ajax/illust/123": '{"error": false, "body": {}}',
    }

    with pytest.raises(ExtractionError, match="no original image"):
        list(Pixiv("https://www.pixiv.net/artworks/123").extract(fake_fetcher(routes)))


@pytest.mark.unit
def test_pixiv_user_gallery_skips_artwork_without_image() -> None:
    # The opposite policy for a gallery: one unavailable work must not abort the
    # traversal, so the avatar still comes through.
    routes = {
        "https://www.pixiv.net/ajax/user/9": (
            '{"error": false, "body": {"name": "artist", '
            '"imageBig": "https://i.pximg.net/avatar.jpg"}}'
        ),
        "https://www.pixiv.net/ajax/user/9/profile/all": (
            '{"error": false, "body": {"illusts": {"123": null}, "manga": {}}}'
        ),
        "https://www.pixiv.net/ajax/illust/123/pages": '{"error": false, "body": []}',
        "https://www.pixiv.net/ajax/illust/123": '{"error": false, "body": {}}',
    }

    items = list(Pixiv("https://www.pixiv.net/users/9").extract(fake_fetcher(routes)))

    assert [item.filename for item in items] == ["avatar.jpg"]


@pytest.mark.unit
def test_pixiv_empty_user_profile_raises() -> None:
    routes = {"https://www.pixiv.net/ajax/user/9": '{"error": false, "body": null}'}

    with pytest.raises(ExtractionError, match="Empty profile body"):
        list(Pixiv("https://www.pixiv.net/users/9").extract(fake_fetcher(routes)))


@pytest.mark.unit
def test_thothub_vip_malformed_metadata_raises() -> None:
    page = '<script type="application/ld+json">{oops}</script>'

    with pytest.raises(ExtractionError) as excinfo:
        parse_video_metadata(page, "https://thothub.vip/video/1/clip/")

    error = excinfo.value
    assert error.category == "protocol"
    assert isinstance(error.cause, ValueError)


@pytest.mark.unit
@pytest.mark.parametrize(
    "payload",
    [
        {"url": "encrypted"},
        {"timestamp": 1700000000},
        "not a mapping",
    ],
)
def test_bunkr_incomplete_api_payload_raises(payload: object) -> None:
    with pytest.raises(ExtractionError, match="missing url or timestamp"):
        decrypt_direct_url(payload, "clip.mp4", "https://apidl.bunkr.ru/api/_001_v2")


@pytest.mark.unit
def test_bunkr_payload_that_decrypts_to_garbage_raises() -> None:
    # A re-keyed or bogus blob decrypts to non-URL bytes; yielding an item with
    # that as its download URL would only fail later, far from the cause.
    with pytest.raises(ExtractionError, match="not an HTTP URL"):
        decrypt_direct_url(
            {"timestamp": 1700000000, "url": base64.b64encode(b"garbage").decode()},
            "clip.mp4",
            "https://apidl.bunkr.ru/api/_001_v2",
        )
