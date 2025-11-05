import pytest
import requests

from megaloader.plugins.bunkr import Bunkr


@pytest.mark.integration
class TestBunkrIntegration:
    def test_album_url_parsing(self, requests_mock) -> None:
        album_url = "https://bunkr.si/a/testalbum"

        album_html = """
        <html><body>
        <a href="/f/file1">File 1</a>
        <a href="/f/file2">File 2</a>
        </body></html>
        """

        file_html = """
        <html>
        <a class="btn btn-main" href="/download/xyz">Download</a>
        <meta property="og:title" content="test.jpg">
        </html>
        """

        requests_mock.get(album_url, text=album_html)
        requests_mock.get("https://bunkr.si/f/file1", text=file_html)
        requests_mock.get("https://bunkr.si/f/file2", text=file_html)

        plugin = Bunkr(album_url)
        items = list(plugin.export())

        assert len(items) == 2
        assert all(item.filename == "test.jpg" for item in items)

    def test_single_file_url_parsing(self, requests_mock) -> None:
        file_url = "https://bunkr.si/f/testfile"

        file_html = """
        <html>
        <a class="btn btn-main" href="/download/abc123">Download</a>
        <meta property="og:title" content="myfile.zip">
        </html>
        """

        requests_mock.get(file_url, text=file_html)

        plugin = Bunkr(file_url)
        items = list(plugin.export())

        assert len(items) == 1
        assert items[0].filename == "myfile.zip"

    def test_filename_extraction_fallback(self, requests_mock) -> None:
        url = "https://bunkr.si/f/test"

        html = """
        <html>
        <a class="btn btn-main" href="/download/xyz">Download</a>
        <script>var ogname = "fallback.mp4";</script>
        </html>
        """

        requests_mock.get(url, text=html)

        plugin = Bunkr(url)
        items = list(plugin.export())

        assert items[0].filename == "fallback.mp4"

    def test_network_error_handling(self, requests_mock) -> None:
        url = "https://bunkr.si/a/error"
        requests_mock.get(url, exc=requests.ConnectionError("failed"))

        plugin = Bunkr(url)
        with pytest.raises(requests.ConnectionError):
            list(plugin.export())


@pytest.mark.integration
class TestBunkrDownloadIntegration:
    def test_file_already_exists_skip(self, tmp_output_dir) -> None:
        import os

        plugin = Bunkr("https://bunkr.si/f/test")

        existing = os.path.join(tmp_output_dir, "exists.txt")
        with open(existing, "w") as f:
            f.write("original")

        result = plugin._download_file_direct(
            "https://example.com/file",
            "exists.txt",
            tmp_output_dir,
            "https://bunkr.si/f/test",
        )

        assert result is True
        with open(existing) as f:
            assert f.read() == "original"
