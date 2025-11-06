import hashlib

import pytest

from megaloader.plugins.gofile import Gofile


@pytest.mark.integration
class TestGofileIntegration:
    def test_token_fetching(self, requests_mock) -> None:
        plugin = Gofile("https://gofile.io/d/testid")

        requests_mock.get(
            "https://gofile.io/dist/js/global.js",
            text='code here .wt = "website_token_xyz" code',
        )
        requests_mock.post(
            "https://api.gofile.io/accounts",
            json={"status": "ok", "data": {"token": "api_token_123"}},
        )

        wt = plugin.website_token
        api = plugin.api_token

        assert wt == "website_token_xyz"
        assert api == "api_token_123"

    def test_export_files(self, requests_mock) -> None:
        plugin = Gofile("https://gofile.io/d/folderid")

        requests_mock.get("https://gofile.io/dist/js/global.js", text='.wt = "wt"')
        requests_mock.post(
            "https://api.gofile.io/accounts",
            json={"status": "ok", "data": {"token": "token"}},
        )
        requests_mock.get(
            "https://api.gofile.io/contents/folderid",
            json={
                "status": "ok",
                "data": {
                    "name": "Test Folder",
                    "children": {
                        "f1": {
                            "type": "file",
                            "name": "file1.txt",
                            "link": "https://srv/f1",
                            "id": "f1",
                            "size": 100,
                        },
                        "f2": {
                            "type": "file",
                            "name": "file2.zip",
                            "link": "https://srv/f2",
                            "id": "f2",
                            "size": 500,
                        },
                    },
                },
            },
        )

        items = list(plugin.export())

        assert len(items) == 2
        assert items[0].filename == "file1.txt"
        assert items[0].album_title == "Test Folder"

        assert items[0].metadata is not None
        assert items[0].metadata["size"] == 100

    def test_password_hashing(self) -> None:
        plugin = Gofile("https://gofile.io/d/test", password="mysecret")

        expected = hashlib.sha256(b"mysecret").hexdigest()
        assert plugin.password_hash == expected
