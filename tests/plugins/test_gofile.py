import hashlib
import os

import pytest

from megaloader.plugin import Item
from megaloader.plugins.gofile import Gofile


class TestGofileURLParsing:
    def test_invalid_url_raises(self):
        with pytest.raises(ValueError, match="Invalid Gofile URL"):
            Gofile("https://gofile.io/invalid-url")

    @pytest.mark.parametrize(
        "url,expected_id",
        [
            ("https://gofile.io/d/ABC123", "ABC123"),
            ("https://gofile.io/f/XYZ-789", "XYZ-789"),
            ("https://gofile.io/d/test_id", "test_id"),
        ],
    )
    def test_content_id_extraction(self, url, expected_id):
        plugin = Gofile(url)
        assert plugin.content_id == expected_id


class TestGofilePasswordHandling:
    def test_password_hash_generation(self):
        plugin = Gofile("https://gofile.io/d/test", password="mypassword")
        assert plugin.password_hash is not None
        assert len(plugin.password_hash) == 64
        expected = hashlib.sha256(b"mypassword").hexdigest()
        assert plugin.password_hash == expected

    def test_no_password_initialization(self):
        plugin = Gofile("https://gofile.io/d/test")
        assert plugin.password_hash is None


class TestGofileTokenFetching:
    """Test lazy loading of authentication tokens."""

    def test_website_token_fetching(self, requests_mock):
        plugin = Gofile("https://gofile.io/d/test")

        js_content = 'some code .wt = "test_token_123" more code'
        requests_mock.get("https://gofile.io/dist/js/global.js", text=js_content)

        token = plugin.website_token
        assert token == "test_token_123"

        second_call = plugin.website_token
        assert second_call == "test_token_123"
        assert requests_mock.call_count == 1

    def test_website_token_missing_raises(self, requests_mock):
        plugin = Gofile("https://gofile.io/d/test")
        requests_mock.get("https://gofile.io/dist/js/global.js", text="no token here")

        with pytest.raises(ConnectionError, match="website token"):
            _ = plugin.website_token

    def test_api_token_creation(self, requests_mock):
        plugin = Gofile("https://gofile.io/d/test")

        requests_mock.post(
            "https://api.gofile.io/accounts",
            json={"status": "ok", "data": {"token": "api_token_xyz"}},
        )

        token = plugin.api_token
        assert token == "api_token_xyz"

        second_call = plugin.api_token
        assert second_call == "api_token_xyz"
        assert requests_mock.call_count == 1

    def test_api_token_creation_fails(self, requests_mock):
        plugin = Gofile("https://gofile.io/d/test")

        requests_mock.post(
            "https://api.gofile.io/accounts", json={"status": "error", "data": {}}
        )

        with pytest.raises(ConnectionError, match="API token"):
            _ = plugin.api_token


class TestGofileExport:
    def test_export_success(self, requests_mock):
        plugin = Gofile("https://gofile.io/d/test123")

        requests_mock.get("https://gofile.io/dist/js/global.js", text='.wt = "wtoken"')
        requests_mock.post(
            "https://api.gofile.io/accounts",
            json={"status": "ok", "data": {"token": "apitoken"}},
        )

        contents_json = {
            "status": "ok",
            "data": {
                "name": "MyFolder",
                "children": {
                    "f1": {
                        "type": "file",
                        "name": "file1.txt",
                        "link": "https://srv.gofile.io/download/f1",
                        "id": "f1",
                        "size": 100,
                    },
                    "f2": {
                        "type": "file",
                        "name": "file2.jpg",
                        "link": "https://srv.gofile.io/download/f2",
                        "id": "f2",
                        "size": 200,
                    },
                },
            },
        }
        requests_mock.get("https://api.gofile.io/contents/test123", json=contents_json)

        items = list(plugin.export())

        assert len(items) == 2
        assert items[0].filename == "file1.txt"
        assert items[0].file_id == "f1"
        assert items[0].album_title == "MyFolder"
        assert items[1].filename == "file2.jpg"

    def test_export_with_password(self, requests_mock):
        plugin = Gofile("https://gofile.io/d/secret", password="pass123")

        requests_mock.get("https://gofile.io/dist/js/global.js", text='.wt = "wt"')
        requests_mock.post(
            "https://api.gofile.io/accounts",
            json={"status": "ok", "data": {"token": "token"}},
        )

        contents_json = {
            "status": "ok",
            "data": {
                "name": "SecretFolder",
                "children": {
                    "f1": {
                        "type": "file",
                        "name": "secret.txt",
                        "link": "https://srv.gofile.io/download/f1",
                        "id": "f1",
                        "size": 50,
                    }
                },
            },
        }

        def check_password(request, context):
            assert "password" in request.qs
            return contents_json

        requests_mock.get("https://api.gofile.io/contents/secret", json=check_password)

        items = list(plugin.export())
        assert len(items) == 1

    def test_export_empty_folder(self, requests_mock):
        plugin = Gofile("https://gofile.io/d/empty")

        requests_mock.get("https://gofile.io/dist/js/global.js", text='.wt = "wt"')
        requests_mock.post(
            "https://api.gofile.io/accounts",
            json={"status": "ok", "data": {"token": "token"}},
        )
        requests_mock.get(
            "https://api.gofile.io/contents/empty",
            json={"status": "ok", "data": {"name": "EmptyFolder"}},
        )

        items = list(plugin.export())
        assert len(items) == 0


class TestGofileDownload:
    """Test file download functionality."""

    def test_download_file_success(self, requests_mock, tmp_output_dir):
        plugin = Gofile("https://gofile.io/d/test")

        requests_mock.get("https://gofile.io/dist/js/global.js", text='.wt = "wt"')
        requests_mock.post(
            "https://api.gofile.io/accounts",
            json={"status": "ok", "data": {"token": "dltoken"}},
        )

        file_content = b"file content here"
        file_url = "https://srv.gofile.io/download/file1"

        def check_cookie(request, context):
            assert "Cookie" in request.headers
            assert "accountToken=dltoken" in request.headers["Cookie"]
            return file_content

        requests_mock.get(file_url, content=check_cookie)

        item = Item(url=file_url, filename="test.txt", file_id="file1")
        result = plugin.download_file(item, tmp_output_dir)

        assert result is True
        output_path = os.path.join(tmp_output_dir, "test.txt")
        assert os.path.exists(output_path)
        with open(output_path, "rb") as f:
            assert f.read() == file_content

    def test_download_file_already_exists(self, tmp_output_dir):
        plugin = Gofile("https://gofile.io/d/test")

        existing_path = os.path.join(tmp_output_dir, "existing.txt")
        with open(existing_path, "w") as f:
            f.write("already here")

        item = Item(
            url="https://srv.gofile.io/download/file1",
            filename="existing.txt",
            file_id="file1",
        )

        # Should return True without re-downloading
        result = plugin.download_file(item, tmp_output_dir)
        assert result is True

        with open(existing_path) as f:
            assert f.read() == "already here"


@pytest.mark.live
class TestGofileLive:
    def test_live_token_fetching(self):
        """Verify we can fetch real tokens from Gofile."""
        plugin = Gofile("https://gofile.io/d/wAKzmW")

        try:
            website_token = plugin.website_token
            assert website_token is not None
            assert len(website_token) > 0

            api_token = plugin.api_token
            assert api_token is not None
            assert len(api_token) > 0

            assert plugin._website_token is not None
            assert plugin._api_token is not None
        except ConnectionError as e:
            pytest.skip(f"Gofile API unreachable: {e}")
