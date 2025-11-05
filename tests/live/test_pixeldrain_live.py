import pytest


@pytest.mark.live
@pytest.mark.downloads_file
class TestPixelDrainLive:
    def test_pixeldrain_single_file(self):
        """Test real PixelDrain file"""
        from megaloader.plugins.pixeldrain import PixelDrain

        url = "https://pixeldrain.com/u/95u1wnsd"

        try:
            plugin = PixelDrain(url)
            items = list(plugin.export())

            assert len(items) == 1
            assert items[0].filename == "eunbi (1).mp4"
            assert items[0].metadata["size"] == 11405500
        except Exception as e:
            pytest.skip(f"PixelDrain file unavailable: {e}")

    def test_pixeldrain_list(self):
        """Test real PixelDrain list"""
        from megaloader.plugins.pixeldrain import PixelDrain

        url = "https://pixeldrain.com/l/nH4ZKt3b"

        try:
            plugin = PixelDrain(url)
            items = list(plugin.export())

            assert len(items) >= 1
            for item in items:
                assert item.filename
                assert item.url
                assert item.file_id
        except Exception as e:
            pytest.skip(f"PixelDrain list unavailable: {e}")
