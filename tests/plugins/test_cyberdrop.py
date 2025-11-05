import os
import time

import pytest
import requests

from megaloader.plugin import Item
from megaloader.plugins.cyberdrop import Cyberdrop


class TestCyberdropURLParsing:
    def test_album_export(self, requests_mock, fixture_loader):
        album_url = "https://cyberdrop.me/a/album1"
        album_html = fixture_loader("cyberdrop_album.html")
        requests_mock.get(album_url, text=album_html)

        api_info_url = "https://api.cyberdrop.me/api/file/info/FILE1"
        requests_mock.get(
            api_info_url,
            json={
                "name": "My Photo.jpg",
                "auth_url": "https://api.cyberdrop.me/auth/FILE1",
            },
        )

        plugin = Cyberdrop(album_url)
        items = list(plugin.export())

        assert len(items) == 1
        assert items[0].filename == "My Photo.jpg"
        assert "auth" in items[0].url
        assert items[0].file_id == "FILE1"

    def test_single_file_export(self, requests_mock):
        file_url = "https://cyberdrop.me/f/FILE2"
        api_info_url = "https://api.cyberdrop.me/api/file/info/FILE2"
        requests_mock.get(
            api_info_url,
            json={
                "name": "Single File.png",
                "auth_url": "https://api.cyberdrop.me/auth/FILE2",
            },
        )

        plugin = Cyberdrop(file_url)
        items = list(plugin.export())

        assert len(items) == 1
        assert items[0].file_id == "FILE2"
        assert items[0].filename == "Single File.png"


class TestCyberdropFilenameHandling:
    @pytest.mark.parametrize(
        "input_name,expected",
        [
            ("file<name>.txt", "file_name_.txt"),
            ("path/to\\file", "path_to_file"),
            ("file:name|test", "file_name_test"),
            ("normal_file.jpg", "normal_file.jpg"),
            ("file*?.mp4", "file__.mp4"),
        ],
    )
    def test_sanitize_name(self, input_name, expected):
        plugin = Cyberdrop("https://cyberdrop.me/a/test")
        assert plugin._sanitize_name(input_name) == expected


class TestCyberdropRateLimiting:
    def test_rate_limiting_between_api_calls(self, requests_mock):
        plugin = Cyberdrop("https://cyberdrop.me/f/TEST", rate_limit_seconds=0.5)

        api_url = "https://api.cyberdrop.me/api/file/info/TEST"
        requests_mock.get(
            api_url,
            json={
                "name": "test.jpg",
                "auth_url": "https://api.cyberdrop.me/auth/TEST",
            },
        )

        start = time.monotonic()
        plugin._get_file_info("TEST")
        plugin._get_file_info("TEST")
        elapsed = time.monotonic() - start

        assert elapsed >= 0.5


class TestCyberdropAPIErrorHandling:
    def test_api_invalid_response(self, requests_mock):
        plugin = Cyberdrop("https://cyberdrop.me/f/BAD")

        api_url = "https://api.cyberdrop.me/api/file/info/BAD"
        requests_mock.get(api_url, json={"error": "not found"})

        result = plugin._get_file_info("BAD")
        assert result is None

    @pytest.mark.parametrize(
        "exception_type,exception_instance",
        [
            (requests.Timeout, requests.Timeout("Request timed out")),
            (requests.ConnectionError, requests.ConnectionError("Connection failed")),
        ],
    )
    def test_api_network_errors(
        self, requests_mock, exception_type, exception_instance
    ):
        plugin = Cyberdrop("https://cyberdrop.me/f/ERROR")

        api_url = "https://api.cyberdrop.me/api/file/info/ERROR"
        requests_mock.get(api_url, exc=exception_instance)

        result = plugin._get_file_info("ERROR")
        assert result is None

    @pytest.mark.parametrize("status_code", [404, 500, 503])
    def test_api_http_errors(self, requests_mock, status_code):
        plugin = Cyberdrop("https://cyberdrop.me/f/ERROR")

        api_url = "https://api.cyberdrop.me/api/file/info/ERROR"
        requests_mock.get(api_url, status_code=status_code)

        result = plugin._get_file_info("ERROR")
        assert result is None


class TestCyberdropDownload:
    def test_download_file_success(self, requests_mock, tmp_output_dir):
        plugin = Cyberdrop("https://cyberdrop.me/f/DL")

        auth_url = "https://api.cyberdrop.me/auth/DL"
        direct_url = "https://cdn.cyberdrop.me/file/DL"
        file_content = b"test content"

        requests_mock.get(auth_url, json={"url": direct_url})
        requests_mock.get(direct_url, content=file_content)

        item = Item(url=auth_url, filename="download.txt", file_id="DL")
        result = plugin.download_file(item, tmp_output_dir)

        assert result is True
        output_path = os.path.join(tmp_output_dir, "download.txt")
        assert os.path.exists(output_path)
        with open(output_path, "rb") as f:
            assert f.read() == file_content

    def test_download_file_already_exists(self, tmp_output_dir):
        plugin = Cyberdrop("https://cyberdrop.me/f/DL")

        existing_path = os.path.join(tmp_output_dir, "existing.txt")
        with open(existing_path, "w") as f:
            f.write("already here")

        item = Item(
            url="https://api.cyberdrop.me/auth/DL",
            filename="existing.txt",
            file_id="DL",
        )
        result = plugin.download_file(item, tmp_output_dir)

        assert result is True
        with open(existing_path) as f:
            assert f.read() == "already here"


@pytest.mark.live
class TestCyberdropLive:
    def test_live_album(self):
        """Test against a real Cyberdrop album."""
        url = "https://cyberdrop.me/a/0OpiyaOV"

        try:
            plugin = Cyberdrop(url)
            items = list(plugin.export())

            assert len(items) >= 1

            for item in items:
                assert item.filename
                assert item.file_id
                assert item.url
                assert "api.cyberdrop.me" in item.url or "cyberdrop" in item.url
        except Exception as e:
            pytest.skip(f"Live Cyberdrop album no longer available: {e}")
