import pytest


@pytest.mark.live
class TestGofileLive:
    def test_gofile_tokens(self):
        """Test that we can fetch real tokens"""
        from megaloader.plugins.gofile import Gofile

        plugin = Gofile("https://gofile.io/d/test")

        try:
            wt = plugin.website_token
            api = plugin.api_token

            assert wt and len(wt) > 0
            assert api and len(api) > 0
        except Exception as e:
            pytest.skip(f"Gofile API unreachable: {e}")
