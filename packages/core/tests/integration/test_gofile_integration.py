import json

import pytest

from megaloader.plugins.gofile import Gofile


@pytest.mark.integration
class TestGofileIntegration:
    def test_export_files(self, requests_mock, fixture_loader) -> None:
        plugin = Gofile("https://gofile.io/d/folderid")

        requests_mock.get(
            "https://gofile.io/dist/js/global.js",
            text=fixture_loader("gofile/global.js"),
        )
        requests_mock.post(
            "https://api.gofile.io/accounts",
            json=json.loads(fixture_loader("gofile/accounts.json")),
        )
        requests_mock.get(
            "https://api.gofile.io/contents/folderid",
            json=json.loads(fixture_loader("gofile/contents.json")),
        )

        items = list(plugin.extract())

        assert len(items) == 2
        assert items[0].filename == "file1.txt"
        assert items[0].collection_name == "Test Folder"
        assert items[0].size_bytes == 100

    def test_password_hashing(self) -> None:
        import hashlib

        plugin = Gofile("https://gofile.io/d/test", password="mysecret")

        expected = hashlib.sha256(b"mysecret").hexdigest()
        assert plugin.password_hash == expected
