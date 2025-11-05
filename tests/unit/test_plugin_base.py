import pytest

from megaloader.plugin import BasePlugin, Item


@pytest.mark.unit
class TestBasePluginContract:
    def test_item_dataclass(self):
        """Verify Item has required fields"""
        item = Item(url="http://example.com/file.txt", filename="test.txt")
        assert item.url
        assert item.filename
        assert item.album_title is None
        assert item.metadata is None

    def test_plugin_requires_url(self):
        """Verify plugins require non-empty URL"""
        with pytest.raises(ValueError):

            class DummyPlugin(BasePlugin):
                def export(self):
                    pass

                def download_file(self, item, output_dir):
                    pass

            DummyPlugin("")

    def test_export_must_be_implemented(self):
        """Verify export is abstract"""
        with pytest.raises(TypeError):

            class BadPlugin(BasePlugin):
                def download_file(self, item, output_dir):
                    pass

            BadPlugin("http://example.com")
