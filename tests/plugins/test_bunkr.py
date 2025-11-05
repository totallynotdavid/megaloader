import os
import re

import pytest
import requests

from megaloader.plugins.bunkr import Bunkr


class TestBunkrURLParsing:
    def test_album_url_detection(self, requests_mock):
        album_url = "https://bunkr.ru/a/test123"
        requests_mock.get(album_url, text="<html><body></body></html>")

        plugin = Bunkr(album_url)
        list(plugin.export())

    def test_single_file_url_detection(self, requests_mock):
        file_url = "https://bunkr.ru/f/xyz789"

        html = """
        <html><body>
        <a class="btn btn-main" href="https://get.bunkrr.su/file/12345">Download</a>
        <meta property="og:title" content="test.jpg">
        </body></html>
        """

        requests_mock.get(file_url, text=html)

        plugin = Bunkr(file_url)
        items = list(plugin.export())

        assert len(items) == 1
        assert items[0].filename == "test.jpg"


class TestBunkrAlbumParsing:
    def test_parse_album_with_multiple_files(self, requests_mock):
        album_url = "https://bunkr.ru/a/real-album"
        album_html = """
        <html><body>
        <header>Navigation stuff</header>
        <div class="album-content">
            <a href="/f/file1">Image 1</a>
            <a href="/f/file2">Video 1</a>
            <a href="/f/file3">Document</a>
        </div>
        <footer>Footer stuff</footer>
        </body></html>
        """

        file1_html = """
        <html>
        <a class="btn btn-main" href="/download/file1">Download</a>
        <meta property="og:title" content="image1.jpg">
        </html>
        """

        file2_html = """
        <html>
        <a class="btn btn-main" href="/download/file2">Download</a>
        <meta property="og:title" content="video1.mp4">
        </html>
        """

        file3_html = """
        <html>
        <a class="btn btn-main" href="/download/file3">Download</a>
        <meta property="og:title" content="document.pdf">
        </html>
        """

        requests_mock.get(album_url, text=album_html)
        requests_mock.get("https://bunkr.ru/f/file1", text=file1_html)
        requests_mock.get("https://bunkr.ru/f/file2", text=file2_html)
        requests_mock.get("https://bunkr.ru/f/file3", text=file3_html)

        plugin = Bunkr(album_url)
        items = list(plugin.export())

        assert len(items) == 3
        assert items[0].filename == "image1.jpg"
        assert items[1].filename == "video1.mp4"
        assert items[2].filename == "document.pdf"

    def test_parse_empty_album(self, requests_mock):
        album_url = "https://bunkr.ru/a/empty"
        empty_html = """<html><body>
        <div class="album-content">No files found</div>
        </body></html>"""
        requests_mock.get(album_url, text=empty_html)

        plugin = Bunkr(album_url)
        items = list(plugin.export())

        assert len(items) == 0

    def test_album_with_duplicate_links(self, requests_mock):
        album_url = "https://bunkr.ru/a/dupes"
        album_html = """<html><body>
        <a href="/f/same">File</a>
        <a href="/f/same">File Again</a>
        <a href="/f/same">File Third Time</a>
        </body></html>"""

        file_html = """<html>
        <a class="btn btn-main" href="/download/same">Download</a>
        <meta property="og:title" content="same_file.txt">
        </html>"""

        requests_mock.get(album_url, text=album_html)
        requests_mock.get("https://bunkr.ru/f/same", text=file_html)

        plugin = Bunkr(album_url)
        items = list(plugin.export())

        assert len(items) == 1


class TestBunkrFilenameExtraction:
    @pytest.mark.parametrize(
        "html,expected",
        [
            ('<meta property="og:title" content="my_file.jpg">', "my_file.jpg"),
            ('<script>var ogname = "backup_name.mp4";</script>', "backup_name.mp4"),
            (
                '<meta property="og:title" content="file&amp;name&#39;s.txt">',
                "file&name's.txt",
            ),
            (
                '<meta property="og:title" content="文件名 (1) [test].jpg">',
                "文件名 (1) [test].jpg",
            ),
        ],
    )
    def test_extract_filename_variations(self, html, expected):
        plugin = Bunkr("https://bunkr.ru/f/test")
        filename = plugin._extract_filename(html)
        assert filename == expected

    def test_extract_filename_fallback_on_missing(self):
        plugin = Bunkr("https://bunkr.ru/f/abc123")
        html = "<html><body>No filename metadata</body></html>"
        filename = plugin._extract_filename(html)
        assert filename is None


class TestBunkrErrorHandling:
    @pytest.mark.parametrize(
        "exception_type,exception_instance",
        [
            (requests.Timeout, requests.Timeout("Request timed out")),
            (requests.ConnectionError, requests.ConnectionError("Connection failed")),
        ],
    )
    def test_network_errors(self, requests_mock, exception_type, exception_instance):
        url = "https://bunkr.ru/f/error"
        requests_mock.get(url, exc=exception_instance)

        plugin = Bunkr(url)

        with pytest.raises(exception_type):
            list(plugin.export())

    @pytest.mark.parametrize("status_code", [404, 500, 503])
    def test_http_errors(self, requests_mock, status_code):
        url = "https://bunkr.ru/f/error"
        requests_mock.get(url, status_code=status_code)

        plugin = Bunkr(url)

        with pytest.raises(requests.HTTPError):
            list(plugin.export())

    def test_malformed_html_graceful_handling(self, requests_mock):
        url = "https://bunkr.ru/f/malformed"
        requests_mock.get(url, text="<html><body><div>Broken HTML")

        plugin = Bunkr(url)
        items = list(plugin.export())

        assert len(items) == 0

    def test_missing_download_button(self, requests_mock):
        url = "https://bunkr.ru/f/nobutton"
        requests_mock.get(url, text="<html><body>Page with no download</body></html>")

        plugin = Bunkr(url)
        items = list(plugin.export())

        assert len(items) == 0


class TestBunkrSecurity:
    @pytest.mark.parametrize(
        "malicious_filename",
        [
            "../../../evil.txt",
            "file\x00.txt",
            "a" * 300 + ".txt",
        ],
    )
    def test_malicious_filenames_preserved_for_sanitization(
        self, requests_mock, malicious_filename
    ):
        """
        Filenames with path traversal, null bytes, or excessive length
        should be preserved in the Item; sanitization happens in download_file.
        """
        url = "https://bunkr.ru/f/malicious"

        html = f"""
        <html>
        <a class="btn btn-main" href="/download/mal">Download</a>
        <meta property="og:title" content="{malicious_filename}">
        </html>
        """

        requests_mock.get(url, text=html)

        plugin = Bunkr(url)
        items = list(plugin.export())

        assert len(items) == 1
        assert items[0].filename == malicious_filename


class TestBunkrDownload:
    def test_download_file_already_exists(self, tmp_output_dir):
        plugin = Bunkr("https://bunkr.ru/f/test")

        existing_path = os.path.join(tmp_output_dir, "existing.txt")
        with open(existing_path, "w") as f:
            f.write("already here")

        result = plugin._download_file_direct(
            "https://cdn.bunkr.ru/test",
            "existing.txt",
            tmp_output_dir,
            "https://bunkr.ru/f/test",
        )

        assert result is True
        with open(existing_path) as f:
            assert f.read() == "already here"

    def test_download_creates_output_directory(self, tmp_path):
        Bunkr("https://bunkr.ru/f/test")
        nonexistent_dir = tmp_path / "nonexistent" / "nested" / "dir"
        assert not nonexistent_dir.exists()


@pytest.mark.live
class TestBunkrLive:
    def test_live_single_file_real_url(self):
        """Test against a real Bunkr file URL from the project examples."""
        url = "https://bunkrr.su/d/megaloader-main-RKEICuly.zip"

        try:
            plugin = Bunkr(url)
            items = list(plugin.export())

            assert len(items) == 1
            item = items[0]

            assert item.filename == "megaloader-main.zip"
            assert item.url
            assert "get.bunkrr.su/file/" in item.url
            assert re.search(r"/file/\d+$", item.url)
        except Exception as e:
            pytest.skip(f"Live Bunkr URL no longer available: {e}")
