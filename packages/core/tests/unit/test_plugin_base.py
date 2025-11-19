import pytest

from megaloader.plugin import BasePlugin, Item


@pytest.mark.unit
class TestBasePluginContract:
    def test_item_dataclass_required_fields(self) -> None:
        """Verify Item requires url and filename."""
        item = Item(url="http://example.com/file.txt", filename="test.txt")
        assert item.url == "http://example.com/file.txt"
        assert item.filename == "test.txt"
        assert item.album is None
        assert item.id is None
        assert item.meta is None

    def test_item_dataclass_optional_fields(self) -> None:
        """Verify Item optional fields work correctly."""
        metadata = {"size": 1024, "type": "image"}
        item = Item(
            url="http://example.com/file.txt",
            filename="test.txt",
            album="Test Album",
            id="12345",
            meta=metadata,
        )
        assert item.album == "Test Album"
        assert item.id == "12345"
        assert item.meta == metadata

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
