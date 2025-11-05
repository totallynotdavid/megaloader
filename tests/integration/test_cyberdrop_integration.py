import time

import pytest

from megaloader.plugin import Item
from megaloader.plugins.cyberdrop import Cyberdrop


@pytest.mark.integration
class TestCyberdropIntegration:
    def test_album_export(self, requests_mock, fixture_loader):
        """Test album page parsing"""
        album_url = "https://cyberdrop.me/a/testalbum"
        album_html = """
        <html><body>
        <h1 id="title">My Album</h1>
        <a class="file" href="/f/ID1">File 1</a>
        <a class="file" href="/f/ID2">File 2</a>
        </body></html>
        """

        api_response = {
            "name": "test_file.jpg",
            "auth_url": "https://api.cyberdrop.me/auth/testid",
        }

        requests_mock.get(album_url, text=album_html)
        requests_mock.get(
            "https://api.cyberdrop.me/api/file/info/ID1", json=api_response
        )
        requests_mock.get(
            "https://api.cyberdrop.me/api/file/info/ID2", json=api_response
        )

        plugin = Cyberdrop(album_url)
        items = list(plugin.export())

        assert len(items) == 2
        assert items[0].album_title == "My Album"
        assert items[0].filename == "test_file.jpg"

    def test_single_file_export(self, requests_mock):
        """Test single file parsing"""
        file_url = "https://cyberdrop.me/f/FILEID"
        api_response = {
            "name": "single.mp4",
            "auth_url": "https://api.cyberdrop.me/auth/FILEID",
        }

        requests_mock.get(
            "https://api.cyberdrop.me/api/file/info/FILEID", json=api_response
        )

        plugin = Cyberdrop(file_url)
        items = list(plugin.export())

        assert len(items) == 1
        assert items[0].filename == "single.mp4"

    def test_rate_limiting(self, requests_mock):
        """Test that rate limiting is applied"""
        plugin = Cyberdrop("https://cyberdrop.me/f/TEST", rate_limit_seconds=0.2)

        requests_mock.get(
            "https://api.cyberdrop.me/api/file/info/TEST",
            json={"name": "file.txt", "auth_url": "https://api.cyberdrop.me/auth/TEST"},
        )

        start = time.monotonic()
        plugin._get_file_info("TEST")
        plugin._get_file_info("TEST")
        elapsed = time.monotonic() - start

        assert elapsed >= 0.2

    def test_download_success(self, requests_mock, tmp_output_dir):
        """Test file download"""
        auth_url = "https://api.cyberdrop.me/auth/DLTEST"
        direct_url = "https://cdn.cyberdrop.me/file/DLTEST"
        file_content = b"downloaded content"

        requests_mock.get(auth_url, json={"url": direct_url})
        requests_mock.get(direct_url, content=file_content)

        plugin = Cyberdrop("https://cyberdrop.me/f/DLTEST")
        item = Item(url=auth_url, filename="test.bin", file_id="DLTEST")

        result = plugin.download_file(item, tmp_output_dir)

        assert result is True

        import os

        path = os.path.join(tmp_output_dir, "test.bin")
        assert os.path.exists(path)
        with open(path, "rb") as f:
            assert f.read() == file_content
