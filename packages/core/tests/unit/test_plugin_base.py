import pytest

from megaloader.plugin import BasePlugin, Item


@pytest.mark.unit
class TestBasePluginContract:
    def test_item_dataclass_required_fields(self) -> None:
        """Verify Item requires url and filename."""
        item = Item(url="http://example.com/file.txt", filename="test.txt")
        assert item.url == "http://example.com/file.txt"
        assert item.filename == "test.txt"
        assert item.album_title is None
        assert item.file_id is None
        assert item.metadata is None

    def test_item_dataclass_optional_fields(self) -> None:
        """Verify Item optional fields work correctly."""
        metadata = {"size": 1024, "type": "image"}
        item = Item(
            url="http://example.com/file.txt",
            filename="test.txt",
            album_title="Test Album",
            file_id="12345",
            metadata=metadata,
        )
        assert item.album_title == "Test Album"
        assert item.file_id == "12345"
        assert item.metadata == metadata

    def test_plugin_requires_non_empty_url(self) -> None:
        with pytest.raises(ValueError, match="URL must be a non-empty string"):

            class DummyPlugin(BasePlugin):
                def export(self):
                    yield from []

                def download_file(self, item, output_dir) -> bool:
                    return True

            DummyPlugin("")

    def test_plugin_requires_url_argument(self) -> None:
        with pytest.raises(TypeError):

            class DummyPlugin(BasePlugin):
                def export(self):
                    yield from []

                def download_file(self, item, output_dir) -> bool:
                    return True

            DummyPlugin()  # type: ignore[reportCallIssue]  # Missing url argument (intentional for test)

    def test_plugin_stores_url(self) -> None:
        """Verify plugin stores and strips URL."""

        class DummyPlugin(BasePlugin):
            def export(self):
                yield from []

            def download_file(self, item, output_dir) -> bool:
                return True

        plugin = DummyPlugin("  http://example.com/test  ")
        assert plugin.url == "http://example.com/test"

    def test_export_method_abstract(self) -> None:
        """Verify export method must be implemented."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):

            class BadPlugin(BasePlugin):
                def download_file(self, item, output_dir) -> bool:
                    return True

            BadPlugin("http://example.com")  # type: ignore[reportAbstractUsage]  # intentional for test

    def test_download_file_method_abstract(self) -> None:
        """Verify download_file method must be implemented."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):

            class BadPlugin(BasePlugin):
                def export(self):
                    yield from []

            BadPlugin("http://example.com")  # type: ignore[reportAbstractUsage]  # intentional for test

    def test_plugin_config_storage(self) -> None:
        class DummyPlugin(BasePlugin):
            def export(self):
                yield from []

            def download_file(self, item, output_dir) -> bool:
                return True

        plugin = DummyPlugin("http://example.com", custom_option="test", timeout=30)
        assert plugin._config["custom_option"] == "test"
        assert plugin._config["timeout"] == 30
