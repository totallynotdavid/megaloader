import pytest

from megaloader.item import DownloadItem
from megaloader.plugin import BasePlugin


@pytest.mark.unit
class TestBasePluginContract:
    def test_item_dataclass_required_fields(self) -> None:
        """Verify DownloadItem requires download_url and filename."""
        item = DownloadItem(
            download_url="http://example.com/file.txt", filename="test.txt"
        )
        assert item.download_url == "http://example.com/file.txt"
        assert item.filename == "test.txt"
        assert item.collection_name is None
        assert item.source_id is None
        assert item.headers == {}
        assert item.size_bytes is None

    def test_item_dataclass_optional_fields(self) -> None:
        """Verify DownloadItem optional fields work correctly."""
        headers = {"Referer": "http://example.com"}
        item = DownloadItem(
            download_url="http://example.com/file.txt",
            filename="test.txt",
            collection_name="Test Album",
            source_id="12345",
            headers=headers,
            size_bytes=1024,
        )
        assert item.collection_name == "Test Album"
        assert item.source_id == "12345"
        assert item.headers == headers
        assert item.size_bytes == 1024

    def test_plugin_requires_non_empty_url(self) -> None:
        with pytest.raises(ValueError, match="URL must be a non-empty string"):

            class DummyPlugin(BasePlugin):
                def extract(self):
                    yield from []

            DummyPlugin("")

    def test_plugin_requires_url_argument(self) -> None:
        with pytest.raises(TypeError):

            class DummyPlugin(BasePlugin):
                def extract(self):
                    yield from []

            DummyPlugin()  # type: ignore[reportCallIssue]  # Missing url argument (intentional for test)

    def test_plugin_stores_url(self) -> None:
        """Verify plugin stores and strips URL."""

        class DummyPlugin(BasePlugin):
            def extract(self):
                yield from []

        plugin = DummyPlugin("  http://example.com/test  ")
        assert plugin.url == "http://example.com/test"

    def test_extract_method_abstract(self) -> None:
        """Verify extract method must be implemented."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):

            class BadPlugin(BasePlugin):
                pass

            BadPlugin("http://example.com")  # type: ignore[reportAbstractUsage]  # intentional for test

    def test_plugin_config_storage(self) -> None:
        class DummyPlugin(BasePlugin):
            def extract(self):
                yield from []

        plugin = DummyPlugin("http://example.com", custom_option="test", timeout=30)
        assert plugin.options["custom_option"] == "test"
        assert plugin.options["timeout"] == 30
