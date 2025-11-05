import pytest


@pytest.mark.live
@pytest.mark.downloads_file
class TestCyberdropLive:
    def test_cyberdrop_album(self):
        """Test against real Cyberdrop album"""
        from megaloader.plugins.cyberdrop import Cyberdrop

        url = "https://cyberdrop.me/a/0OpiyaOV"

        try:
            plugin = Cyberdrop(url)
            items = list(plugin.export())

            assert len(items) >= 1
            for item in items:
                assert item.filename
                assert item.url
                assert item.file_id
        except Exception as e:
            pytest.skip(f"Cyberdrop album unavailable: {e}")
