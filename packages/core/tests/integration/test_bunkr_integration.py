import pytest
import requests

from megaloader.plugins.bunkr import Bunkr


@pytest.mark.integration
class TestBunkrIntegration:
    def test_album_url_parsing(self, requests_mock, fixture_loader) -> None:
        album_url = "https://bunkr.si/a/testalbum"

        album_html = fixture_loader("bunkr/album.html")

        file_html = fixture_loader("bunkr/file.html")

        requests_mock.get(album_url, text=album_html)
        requests_mock.get("https://bunkr.si/f/file1", text=file_html)
        requests_mock.get("https://bunkr.si/f/file2", text=file_html)

        plugin = Bunkr(album_url)
        items = list(plugin.extract())

        assert len(items) == 2
        assert all(item.filename == "test.jpg" for item in items)

    def test_single_file_url_parsing(self, requests_mock, fixture_loader) -> None:
        file_url = "https://bunkr.si/f/testfile"

        file_html = fixture_loader("bunkr/file.html")

        requests_mock.get(file_url, text=file_html)

        plugin = Bunkr(file_url)
        items = list(plugin.extract())

        assert len(items) == 1
        assert items[0].filename == "test.jpg"

    def test_filename_extraction_fallback(self, requests_mock, fixture_loader) -> None:
        url = "https://bunkr.si/f/test"

        html = fixture_loader("bunkr/fallback.html")

        requests_mock.get(url, text=html)

        plugin = Bunkr(url)
        items = list(plugin.extract())

        assert items[0].filename == "fallback.mp4"

    def test_network_error_handling(self, requests_mock) -> None:
        url = "https://bunkr.si/a/error"
        requests_mock.get(url, exc=requests.ConnectionError("failed"))

        plugin = Bunkr(url)
        with pytest.raises(requests.ConnectionError):
            list(plugin.extract())
