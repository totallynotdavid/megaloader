from typing import cast

import pytest

from megaloader import extract
from megaloader.exceptions import ExtractionError, UnsupportedDomainError
from megaloader.item import DownloadItem
from megaloader.plugin import BasePlugin


class DummyPlugin(BasePlugin):
    def extract(self, fetch):
        yield DownloadItem(
            download_url="https://example.com/file.txt",
            filename="file.txt",
        )


class ExplodingPlugin(BasePlugin):
    def extract(self, fetch):
        msg = "boom"
        raise RuntimeError(msg)
        yield


class ExtractionErrorPlugin(BasePlugin):
    def extract(self, fetch):
        msg = "already normalized"
        raise ExtractionError(msg, source="dummy", category="protocol")
        yield


@pytest.mark.unit
def test_extract_supports_explicit_plugin_name_override() -> None:
    generator = extract("https://unknown.example/path", plugin="gofile")
    assert generator is not None


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


@pytest.mark.unit
@pytest.mark.parametrize("url", ["", "   "])
def test_extract_rejects_blank_url(url: str) -> None:
    with pytest.raises(ValueError, match="URL cannot be empty"):
        list(extract(url))


@pytest.mark.unit
def test_extract_rejects_url_without_a_domain() -> None:
    with pytest.raises(ValueError, match="Could not parse domain"):
        list(extract("not-a-url"))


@pytest.mark.unit
def test_extract_trims_surrounding_whitespace() -> None:
    items = list(extract("  https://unknown.example/path  ", plugin=DummyPlugin))

    assert len(items) == 1


@pytest.mark.unit
def test_extract_wraps_unexpected_plugin_errors() -> None:
    # Anything a plugin raises that is not already an ExtractionError has to be
    # normalized, so callers only ever handle megaloader's own error type.
    with pytest.raises(ExtractionError) as exc_info:
        list(extract("https://unknown.example/path", plugin=ExplodingPlugin))

    err = exc_info.value
    assert err.category == "unknown"
    assert err.source == "explodingplugin"
    assert err.url == "https://unknown.example/path"
    assert isinstance(err.cause, RuntimeError)


@pytest.mark.unit
def test_extract_propagates_plugin_extraction_errors_unchanged() -> None:
    with pytest.raises(ExtractionError) as exc_info:
        list(extract("https://unknown.example/path", plugin=ExtractionErrorPlugin))

    assert exc_info.value.detail == "already normalized"
    assert exc_info.value.category == "protocol"
