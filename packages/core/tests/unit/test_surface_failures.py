"""Provider responses with invalid shapes must raise extraction errors."""

import base64
import json

from collections.abc import Mapping

import pytest
import requests

from megaloader.exceptions import ExtractionError
from megaloader.fetcher import Request, RequestsFetcher, Response
from megaloader.plugin import BasePlugin
from megaloader.plugins.bunkr import Bunkr
from megaloader.plugins.cyberdrop import Cyberdrop
from megaloader.plugins.gofile import Gofile
from megaloader.plugins.pixeldrain import PixelDrain
from megaloader.plugins.pixiv import Pixiv
from megaloader.plugins.rule34 import Rule34
from megaloader.plugins.thothub_to import ThothubTO
from megaloader.plugins.thothub_vip import ThothubVIP

from tests.helpers import fake_fetcher


def _run(plugin: BasePlugin, routes: dict[str, str]) -> None:
    list(plugin.extract(fake_fetcher(routes)))


class _CannedAdapter(requests.adapters.BaseAdapter):
    def send(self, request, **kwargs):  # type: ignore[no-untyped-def]
        raw = requests.Response()
        raw.status_code = 200
        raw.url = request.url
        raw._content = b"<html>Just a moment...</html>"
        raw.encoding = "utf-8"
        return raw

    def close(self) -> None:
        pass


@pytest.mark.unit
def test_non_json_body_raises_protocol_error() -> None:
    session = requests.Session()
    session.mount("https://", _CannedAdapter())
    fetch = RequestsFetcher("bunkr", session=session)

    response = fetch(Request("https://api.example.com/v1"))
    with pytest.raises(ExtractionError) as excinfo:
        response.json()

    error = excinfo.value
    assert error.category == "protocol"
    assert error.source == "bunkr"
    assert error.url == "https://api.example.com/v1"
    assert error.http_status == 200
    assert isinstance(error.cause, ValueError)


@pytest.mark.unit
def test_json_body_still_decodes() -> None:
    response = Response("https://x.test", 200, '{"a": 1}', b'{"a": 1}')

    assert response.json() == {"a": 1}


@pytest.mark.unit
@pytest.mark.parametrize(
    ("plugin", "url"),
    [
        (Bunkr, "https://bunkr.si/v/something"),
        (Cyberdrop, "https://cyberdrop.cr/v/something"),
        (ThothubTO, "https://thothub.to/categories/something/"),
        (ThothubVIP, "https://thothub.vip/categories/something/"),
    ],
)
def test_unrecognized_url_shape_raises_value_error(
    plugin: type[BasePlugin], url: str
) -> None:
    with pytest.raises(ValueError, match="Unrecognized"):
        _run(plugin(url), {})


_RULE34_LISTING = "https://rule34.xxx/index.php?page=post&s=list&tags=foo"
_RULE34_API = "https://api.rule34.xxx/index.php"


def _rule34_api() -> Rule34:
    return Rule34(_RULE34_LISTING, api_key="k", user_id="1")


@pytest.mark.unit
def test_rule34_api_non_xml_body_raises() -> None:
    with pytest.raises(ExtractionError) as excinfo:
        _run(_rule34_api(), {_RULE34_API: "maintenance in progress"})

    assert excinfo.value.category == "protocol"
    assert excinfo.value.url == _RULE34_API


@pytest.mark.unit
def test_rule34_api_empty_page_ends_pagination() -> None:
    routes = {_RULE34_API: '<?xml version="1.0"?><posts count="0" offset="0"/>'}

    assert list(_rule34_api().extract(fake_fetcher(routes))) == []


_BUNKR_FILE = "https://bunkr.si/f/abc"
_BUNKR_API = Bunkr.API_BASE
_BUNKR_PAGE = (
    '<meta property="og:title" content="clip.mp4">'
    '<a class="btn btn-main" href="https://get.bunkrr.su/file/123">Download</a>'
)


def _bunkr_routes(api_body: str) -> dict[str, str]:
    return {_BUNKR_FILE: _BUNKR_PAGE, _BUNKR_API: api_body}


def _bunkr_blob(plaintext: bytes, timestamp: int) -> str:
    key = f"SECRET_KEY_{timestamp // 3600}".encode()
    xored = bytes(b ^ key[i % len(key)] for i, b in enumerate(plaintext))
    return base64.b64encode(xored).decode()


@pytest.mark.unit
def test_bunkr_decrypts_valid_payload() -> None:
    payload = {
        "timestamp": 1700000000,
        "url": _bunkr_blob(b"https://cdn.bunkr.ru/clip.mp4", 1700000000),
    }

    items = list(
        Bunkr(_BUNKR_FILE).extract(fake_fetcher(_bunkr_routes(json.dumps(payload))))
    )

    assert [item.download_url for item in items] == [
        "https://cdn.bunkr.ru/clip.mp4?n=clip.mp4"
    ]


@pytest.mark.unit
@pytest.mark.parametrize(
    "body",
    [
        '{"url": "abcd"}',
        '{"timestamp": 1700000000}',
        '{"timestamp": 1700000000, "url": ""}',
        '{"timestamp": "soon", "url": "abcd"}',
        '["not", "a", "mapping"]',
        '{"timestamp": 1700000000, "url": "***not base64***"}',
    ],
)
def test_bunkr_incomplete_api_payload_raises(body: str) -> None:
    with pytest.raises(ExtractionError) as excinfo:
        _run(Bunkr(_BUNKR_FILE), _bunkr_routes(body))

    assert excinfo.value.category == "protocol"
    assert excinfo.value.source == "bunkr"


@pytest.mark.unit
def test_bunkr_blob_that_decrypts_to_non_url_raises() -> None:
    payload = {
        "timestamp": 1700000000,
        "url": _bunkr_blob(b"definitely not a url", 1700000000),
    }

    with pytest.raises(ExtractionError, match="not an HTTP URL"):
        _run(Bunkr(_BUNKR_FILE), _bunkr_routes(json.dumps(payload)))


_GOFILE_ACCOUNTS = "https://api.gofile.io/accounts"
_GOFILE_CONTENTS = "https://api.gofile.io/contents/abc123"


@pytest.fixture
def gofile_guest(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GOFILE_TOKEN", raising=False)
    monkeypatch.setattr("megaloader.plugins.gofile._token_cache", {})


@pytest.mark.unit
def test_gofile_guest_response_without_token_raises(gofile_guest: None) -> None:
    routes = {_GOFILE_ACCOUNTS: '{"status": "ok", "data": {}}'}

    with pytest.raises(ExtractionError) as excinfo:
        _run(Gofile("https://gofile.io/d/abc123"), routes)

    assert excinfo.value.category == "protocol"
    assert excinfo.value.url == _GOFILE_ACCOUNTS


@pytest.mark.unit
@pytest.mark.parametrize(
    "body",
    [
        '["not", "a", "mapping"]',
        '{"status": "ok", "data": "oops"}',
        '{"status": "ok", "data": ["token"]}',
        '{"status": "ok", "data": null}',
    ],
)
def test_gofile_guest_response_with_wrong_shape_raises(
    gofile_guest: None, body: str
) -> None:
    with pytest.raises(ExtractionError) as excinfo:
        _run(Gofile("https://gofile.io/d/abc123"), {_GOFILE_ACCOUNTS: body})

    assert excinfo.value.category == "protocol"
    assert excinfo.value.url == _GOFILE_ACCOUNTS


def _gofile_contents_body(body: object) -> dict[str, str]:
    return {
        _GOFILE_ACCOUNTS: '{"status": "ok", "data": {"token": "t"}}',
        _GOFILE_CONTENTS: json.dumps(body),
    }


def _gofile_contents(child: object) -> dict[str, str]:
    body = {"status": "ok", "data": {"name": "folder", "children": {"1": child}}}
    return _gofile_contents_body(body)


@pytest.mark.unit
@pytest.mark.parametrize(
    "body",
    [
        ["not", "a", "mapping"],
        {"status": "ok", "data": "oops"},
        {"status": "ok", "data": {"name": "folder", "children": ["a.mp4"]}},
        {"status": "ok"},
        {"status": "ok", "data": {"name": "folder"}},
    ],
)
def test_gofile_contents_with_wrong_shape_raises(
    gofile_guest: None, body: object
) -> None:
    with pytest.raises(ExtractionError) as excinfo:
        _run(Gofile("https://gofile.io/d/abc123"), _gofile_contents_body(body))

    assert excinfo.value.category == "protocol"
    assert excinfo.value.url == _GOFILE_CONTENTS


@pytest.mark.unit
@pytest.mark.parametrize(
    "child",
    [
        {"id": "1", "name": "a.mp4", "link": "https://x/a.mp4"},
        {"type": "", "id": "1"},
        {"type": None, "id": "1"},
    ],
)
def test_gofile_child_entry_without_type_raises(
    gofile_guest: None, child: object
) -> None:
    with pytest.raises(ExtractionError) as excinfo:
        _run(Gofile("https://gofile.io/d/abc123"), _gofile_contents(child))

    assert excinfo.value.category == "protocol"
    assert "type" in excinfo.value.detail


@pytest.mark.unit
def test_gofile_empty_children_is_an_empty_folder(gofile_guest: None) -> None:
    body = {"status": "ok", "data": {"name": "folder", "children": {}}}

    plugin = Gofile("https://gofile.io/d/abc123")

    assert list(plugin.extract(fake_fetcher(_gofile_contents_body(body)))) == []


@pytest.mark.unit
@pytest.mark.parametrize("child", ["a.mp4", None, ["a.mp4"], 7])
def test_gofile_child_entry_that_is_not_a_mapping_raises(
    gofile_guest: None, child: object
) -> None:
    with pytest.raises(ExtractionError) as excinfo:
        _run(Gofile("https://gofile.io/d/abc123"), _gofile_contents(child))

    assert excinfo.value.category == "protocol"
    assert excinfo.value.url == _GOFILE_CONTENTS


@pytest.mark.unit
@pytest.mark.parametrize("missing", ["link", "name", "id"])
def test_gofile_file_entry_missing_field_raises(
    gofile_guest: None, missing: str
) -> None:
    child = {"type": "file", "id": "1", "name": "a.mp4", "link": "https://x/a.mp4"}
    del child[missing]

    with pytest.raises(ExtractionError) as excinfo:
        _run(Gofile("https://gofile.io/d/abc123"), _gofile_contents(child))

    assert excinfo.value.category == "protocol"
    assert missing in excinfo.value.detail


@pytest.mark.unit
def test_gofile_folder_entries_are_not_validated_as_files(gofile_guest: None) -> None:
    routes = _gofile_contents({"type": "folder", "id": "2"})

    assert (
        list(Gofile("https://gofile.io/d/abc123").extract(fake_fetcher(routes))) == []
    )


_PIXELDRAIN = "https://pixeldrain.com/l/abc123"


def _pixeldrain_page(viewer_data: str) -> dict[str, str]:
    return {_PIXELDRAIN: f"<script>window.viewer_data = {viewer_data};</script>"}


@pytest.mark.unit
def test_pixeldrain_malformed_viewer_data_raises() -> None:
    with pytest.raises(ExtractionError) as excinfo:
        _run(PixelDrain(_PIXELDRAIN), _pixeldrain_page("{not json}"))

    assert excinfo.value.category == "protocol"
    assert isinstance(excinfo.value.cause, ValueError)


@pytest.mark.unit
@pytest.mark.parametrize(
    "viewer_data",
    [
        '{"type": "list", "api_response": {}}',
        '{"type": "list", "api_response": {"files": [{"name": "a.jpg"}]}}',
        '{"type": "list", "api_response": {"files": [{"id": "a"}]}}',
        '{"type": "file", "api_response": {"name": "a.jpg"}}',
        '{"type": "file", "api_response": {"id": "a"}}',
        '{"type": "list", "api_response": {"files": {}}}',
        '{"type": "list", "api_response": {"files": "a.jpg"}}',
        '{"type": "list", "api_response": {"files": null}}',
        '{"type": "list", "api_response": {"files": ["a.jpg"]}}',
        '{"type": "list", "api_response": {"files": [null]}}',
        '{"type": "list", "api_response": {"files": [[]]}}',
        '{"type": "list", "api_response": "oops"}',
        '{"type": "list", "api_response": null}',
    ],
)
def test_pixeldrain_changed_viewer_data_raises(viewer_data: str) -> None:
    with pytest.raises(ExtractionError) as excinfo:
        _run(PixelDrain(_PIXELDRAIN), _pixeldrain_page(viewer_data))

    assert excinfo.value.category == "protocol"


@pytest.mark.unit
def test_pixeldrain_empty_list_is_an_empty_album() -> None:
    routes = _pixeldrain_page('{"type": "list", "api_response": {"files": []}}')

    assert list(PixelDrain(_PIXELDRAIN).extract(fake_fetcher(routes))) == []


@pytest.mark.unit
def test_thothub_vip_malformed_metadata_raises() -> None:
    url = "https://thothub.vip/video/1/clip/"
    page = '<script type="application/ld+json">{oops}</script>'

    with pytest.raises(ExtractionError) as excinfo:
        _run(ThothubVIP(url), {url: page})

    assert excinfo.value.category == "protocol"
    assert isinstance(excinfo.value.cause, ValueError)


_PIXIV = "https://www.pixiv.net/ajax"
_NO_IMAGE_ROUTES = {
    f"{_PIXIV}/illust/123/pages": '{"error": false, "body": []}',
    f"{_PIXIV}/illust/123": '{"error": false, "body": {}}',
}


@pytest.mark.unit
def test_pixiv_requested_artwork_without_image_raises() -> None:
    with pytest.raises(ExtractionError) as excinfo:
        _run(Pixiv("https://www.pixiv.net/artworks/123"), _NO_IMAGE_ROUTES)

    assert excinfo.value.category == "protocol"


@pytest.mark.unit
def test_pixiv_user_gallery_skips_unavailable_artwork() -> None:
    routes = {
        f"{_PIXIV}/user/9": (
            '{"error": false, "body": {"name": "artist", '
            '"imageBig": "https://i.pximg.net/avatar.jpg"}}'
        ),
        f"{_PIXIV}/user/9/profile/all": (
            '{"error": false, "body": {"illusts": {"123": null}, "manga": {}}}'
        ),
        **_NO_IMAGE_ROUTES,
    }

    items = list(Pixiv("https://www.pixiv.net/users/9").extract(fake_fetcher(routes)))

    assert [item.filename for item in items] == ["avatar.jpg"]


_NOT_TEXT = [7, ["x"]]


@pytest.mark.unit
@pytest.mark.parametrize("field", ["type", "link", "name", "id"])
@pytest.mark.parametrize("value", _NOT_TEXT)
def test_gofile_file_entry_field_that_is_not_text_raises(
    gofile_guest: None, field: str, value: object
) -> None:
    child = {"type": "file", "id": "1", "name": "a.mp4", "link": "https://x/a.mp4"}
    child[field] = value  # type: ignore[assignment]

    with pytest.raises(ExtractionError) as excinfo:
        _run(Gofile("https://gofile.io/d/abc123"), _gofile_contents(child))

    assert excinfo.value.category == "protocol"
    assert field in excinfo.value.detail


@pytest.mark.unit
@pytest.mark.parametrize("field", ["id", "name"])
@pytest.mark.parametrize("value", _NOT_TEXT)
@pytest.mark.parametrize("shape", ["list", "file"])
def test_pixeldrain_file_field_that_is_not_text_raises(
    field: str, value: object, shape: str
) -> None:
    entry = {"id": "a", "name": "a.jpg", field: value}
    api_response = {"files": [entry]} if shape == "list" else entry
    viewer_data = json.dumps({"type": shape, "api_response": api_response})

    with pytest.raises(ExtractionError) as excinfo:
        _run(PixelDrain(_PIXELDRAIN), _pixeldrain_page(viewer_data))

    assert excinfo.value.category == "protocol"


_CYBERDROP_FILE = "https://cyberdrop.cr/f/xyz123"
_CYBERDROP_INFO = "https://api.cyberdrop.cr/api/file/info/xyz123"
_CYBERDROP_AUTH = "https://api.cyberdrop.cr/auth/xyz123"


def _cyberdrop_routes(info: Mapping[str, object], auth: object) -> dict[str, str]:
    return {_CYBERDROP_INFO: json.dumps(info), _CYBERDROP_AUTH: json.dumps(auth)}


@pytest.mark.unit
@pytest.mark.parametrize("field", ["name", "auth_url"])
@pytest.mark.parametrize("value", _NOT_TEXT)
def test_cyberdrop_info_field_that_is_not_text_raises(
    field: str, value: object
) -> None:
    info = {"name": "a.mp4", "auth_url": _CYBERDROP_AUTH, field: value}

    with pytest.raises(ExtractionError) as excinfo:
        _run(
            Cyberdrop(_CYBERDROP_FILE),
            _cyberdrop_routes(info, {"url": "https://cdn.example.com/a.mp4"}),
        )

    assert excinfo.value.category == "protocol"


@pytest.mark.unit
@pytest.mark.parametrize("value", ["", 7, ["x"]])
def test_cyberdrop_auth_url_that_is_not_text_raises(value: object) -> None:
    info = {"name": "a.mp4", "auth_url": _CYBERDROP_AUTH}

    with pytest.raises(ExtractionError) as excinfo:
        _run(Cyberdrop(_CYBERDROP_FILE), _cyberdrop_routes(info, {"url": value}))

    assert excinfo.value.category == "protocol"


@pytest.mark.unit
@pytest.mark.parametrize("value", _NOT_TEXT)
def test_thothub_vip_content_url_that_is_not_text_raises(value: object) -> None:
    url = "https://thothub.vip/video/1/clip/"
    metadata = json.dumps({"contentUrl": value, "name": "clip"})
    page = f'<script type="application/ld+json">{metadata}</script>'

    with pytest.raises(ExtractionError) as excinfo:
        _run(ThothubVIP(url), {url: page})

    assert excinfo.value.category == "protocol"


@pytest.mark.unit
@pytest.mark.parametrize("value", _NOT_TEXT)
def test_pixiv_original_url_that_is_not_text_raises(value: object) -> None:
    routes = {
        f"{_PIXIV}/illust/123/pages": json.dumps(
            {"error": False, "body": [{"urls": {"original": value}}]}
        ),
        f"{_PIXIV}/illust/123": '{"error": false, "body": {"userName": "a"}}',
    }

    with pytest.raises(ExtractionError) as excinfo:
        _run(Pixiv("https://www.pixiv.net/artworks/123"), routes)

    assert excinfo.value.category == "protocol"


@pytest.mark.unit
@pytest.mark.parametrize(
    "profile",
    [
        {"name": "artist", "imageBig": 7},
        {"name": "artist", "imageBig": ["x"]},
        {"name": "artist", "background": {"url": 7}},
        {"name": "artist", "background": {"url": ["x"]}},
    ],
)
def test_pixiv_profile_image_that_is_not_text_raises(
    profile: dict[str, object],
) -> None:
    routes = {f"{_PIXIV}/user/9": json.dumps({"error": False, "body": profile})}

    with pytest.raises(ExtractionError) as excinfo:
        _run(Pixiv("https://www.pixiv.net/users/9"), routes)

    assert excinfo.value.category == "protocol"


_SKIP_WARNING = "Skipping artwork"


@pytest.mark.unit
def test_pixiv_requested_artwork_raises_without_skip_warning(
    caplog: pytest.LogCaptureFixture,
) -> None:
    with caplog.at_level("WARNING"), pytest.raises(ExtractionError):
        _run(Pixiv("https://www.pixiv.net/artworks/123"), _NO_IMAGE_ROUTES)

    assert _SKIP_WARNING not in caplog.text


@pytest.mark.unit
def test_pixiv_gallery_warns_when_skipping_artwork(
    caplog: pytest.LogCaptureFixture,
) -> None:
    routes = {
        f"{_PIXIV}/user/9": '{"error": false, "body": {"name": "artist"}}',
        f"{_PIXIV}/user/9/profile/all": (
            '{"error": false, "body": {"illusts": {"123": null}, "manga": {}}}'
        ),
        **_NO_IMAGE_ROUTES,
    }

    with caplog.at_level("WARNING"):
        _run(Pixiv("https://www.pixiv.net/users/9"), routes)

    assert f"{_SKIP_WARNING} 123" in caplog.text
