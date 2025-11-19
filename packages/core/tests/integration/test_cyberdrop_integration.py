import pytest

from megaloader.plugins.cyberdrop import Cyberdrop


@pytest.mark.integration
class TestCyberdropIntegration:
    def test_album_export(self, requests_mock, fixture_loader) -> None:
        album_url = "https://cyberdrop.me/a/testalbum"

        album_html = """
        <html><body>
        <h1 id="title">An album</h1>
        <a class="file" href="/f/ID1">File 1</a>
        <a class="file" href="/f/ID2">File 2</a>
        </body></html>
        """

        api_response = {
            "name": "test_file.jpg",
            "auth_url": "https://api.cyberdrop.cr/auth/testid",
        }

        requests_mock.get(album_url, text=album_html)
        requests_mock.get(
            "https://api.cyberdrop.cr/api/file/info/ID1",
            json=api_response,
        )
        requests_mock.get(
            "https://api.cyberdrop.cr/api/file/info/ID2",
            json=api_response,
        )

        plugin = Cyberdrop(album_url)
        items = list(plugin.extract())

        assert len(items) == 2
        assert items[0].album == "An album"
        assert items[0].filename == "test_file.jpg"

    def test_single_file_extract(self, requests_mock) -> None:
        file_url = "https://cyberdrop.me/f/FILEID"

        api_response = {
            "name": "single.mp4",
            "auth_url": "https://api.cyberdrop.cr/auth/FILEID",
        }

        requests_mock.get(
            "https://api.cyberdrop.cr/api/file/info/FILEID",
            json=api_response,
        )

        plugin = Cyberdrop(file_url)
        items = list(plugin.extract())

        assert len(items) == 1
        assert items[0].filename == "single.mp4"
