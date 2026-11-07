from typing import cast

import pytest
import requests_mock as req_mock

from megaloader import extract
from megaloader.exceptions import UnsupportedDomainError
from megaloader.item import DownloadItem
from megaloader.plugin import BasePlugin


class DummyPlugin(BasePlugin):
    def extract(self, fetch):
        yield DownloadItem(
            download_url="https://example.com/file.txt",
            filename="file.txt",
        )


@pytest.mark.unit
def test_extract_resolves_plugin_by_name() -> None:
    with pytest.raises(ValueError, match="Invalid Gofile URL"):
        list(extract("https://unknown.example/path", plugin="gofile"))


@pytest.mark.unit
def test_extract_supports_explicit_plugin_class_override() -> None:
    items = list(extract("https://unknown.example/path", plugin=DummyPlugin))
    assert len(items) == 1
    assert items[0].filename == "file.txt"


@pytest.mark.unit
def test_extract_rejects_unknown_plugin_name() -> None:
    with pytest.raises(ValueError, match="Unknown plugin name"):
        list(extract("https://example.com", plugin="missing"))


@pytest.mark.unit
def test_extract_rejects_non_plugin_class_override() -> None:
    invalid_plugin = cast("type[BasePlugin]", str)
    with pytest.raises(TypeError, match="must inherit from BasePlugin"):
        list(extract("https://example.com", plugin=invalid_plugin))


@pytest.mark.unit
def test_extract_raises_for_unknown_domain_without_override() -> None:
    with pytest.raises(UnsupportedDomainError):
        list(extract("https://unknown.example/path"))


_PIXELDRAIN_PAGE = (
    '<script>window.viewer_data = {"type": "file", '
    '"api_response": {"id": "abc", "name": "a.txt"}};</script>'
)


@pytest.mark.unit
@pytest.mark.parametrize(
    "url",
    [
        "https://pixeldrain.com:443/u/abc",
        "https://user@pixeldrain.com/u/abc",
        "https://PixelDrain.com/u/abc",
    ],
)
def test_extract_resolves_the_plugin_from_the_host_alone(
    requests_mock: req_mock.Mocker, url: str
) -> None:
    requests_mock.get(url, text=_PIXELDRAIN_PAGE)

    items = list(extract(url))

    assert [item.filename for item in items] == ["a.txt"]
