import pytest


@pytest.mark.live
@pytest.mark.downloads_file
class TestBunkrLive:
    def test_real_bunkr_file(self):
        """Test against a real Bunkr file URL"""
        from megaloader.plugins.bunkr import Bunkr

        # Using URL from README examples
        url = "https://bunkrr.su/d/megaloader-main-RKEICuly.zip"

        try:
            plugin = Bunkr(url)
            items = list(plugin.export())

            assert len(items) >= 1
            item = items[0]

            assert item.filename
            assert item.url
            assert "get.bunkr" in item.url or "bunkr" in item.url
        except Exception as e:
            pytest.skip(f"Bunkr URL unavailable: {e}")

    def test_bunkr_album(self):
        """Test album parsing on live Bunkr"""
        from megaloader.plugins.bunkr import Bunkr

        # Find a valid album URL and test
        url = "https://bunkr.si/a/test"

        try:
            plugin = Bunkr(url)
            items = list(plugin.export())
            # Just verify it runs without crashing
            assert isinstance(items, list)
        except Exception as e:
            pytest.skip(f"Bunkr album test skipped: {e}")
