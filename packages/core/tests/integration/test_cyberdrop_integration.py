import json

import pytest

from megaloader.plugins.cyberdrop import Cyberdrop


@pytest.mark.integration
class TestCyberdropIntegration:
    def test_album_export(self, requests_mock, fixture_loader) -> None:
        album_url = "https://cyberdrop.me/a/testalbum"

        album_html = fixture_loader("cyberdrop/album.html")

        api_response = json.loads(fixture_loader("cyberdrop/api.json"))

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
        assert items[0].collection_name == "An album"
        assert items[0].filename == "test_file.jpg"

    def test_single_file_extract(self, requests_mock, fixture_loader) -> None:
        file_url = "https://cyberdrop.me/f/FILEID"

        api_response = json.loads(fixture_loader("cyberdrop/api.json"))

        requests_mock.get(
            "https://api.cyberdrop.cr/api/file/info/FILEID",
            json=api_response,
        )

        plugin = Cyberdrop(file_url)
        items = list(plugin.extract())

        assert len(items) == 1
        assert items[0].filename == "test_file.jpg"
