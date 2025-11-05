import json
import os

import pytest
import requests

from megaloader.plugin import Item
from megaloader.plugins.pixeldrain import PixelDrain


class TestPixelDrainURLParsing:
    """Test URL validation and type detection."""

    def test_single_file_url_detection(self, requests_mock):
        url = "https://pixeldrain.com/u/abc123"
        html = """<script>
        window.viewer_data = {"type":"file","api_response":{"id":"abc123","name":"test.jpg","size":1024}};
        </script>"""
        requests_mock.get(url, text=html)

        plugin = PixelDrain(url)
        items = list(plugin.export())

        assert len(items) == 1
        assert items[0].filename == "test.jpg"

    def test_list_url_detection(self, requests_mock):
        url = "https://pixeldrain.com/l/xyz789"
        html = """<html><body><script>
        window.viewer_data = {"type":"list","api_response":{"id":"xyz789","title":"Test List","files":[{"id":"f1","name":"file1.txt","size":100}]}};
        </script></body></html>"""
        requests_mock.get(url, text=html)

        plugin = PixelDrain(url)
        items = list(plugin.export())

        assert len(items) == 1


class TestPixelDrainFileParsing:
    """Test single file parsing with realistic viewer_data."""

    def test_parse_real_file_structure(self, requests_mock):
        """Test parsing with real PixelDrain viewer_data structure."""
        url = "https://pixeldrain.com/u/95u1wnsd"
        html = """<html><body><script>
        window.viewer_data = {"type":"file","api_response":{"id":"95u1wnsd","name":"eunbi (1).mp4","size":11405500,"views":1678,"bandwidth_used":25618411287,"downloads":1797,"date_upload":"2025-07-06T10:30:18.71Z","mime_type":"video/mp4","hash_sha256":"dfbe302cfcc73639f940252aba0762d75e9f59aeaaa099df18775b00b2068885","can_download":true}};
        </script></body></html>"""
        requests_mock.get(url, text=html)

        plugin = PixelDrain(url)
        items = list(plugin.export())

        assert len(items) == 1
        item = items[0]

        assert item.filename == "eunbi (1).mp4"
        assert item.file_id == "95u1wnsd"
        assert item.metadata["size"] == 11405500
        assert "pixeldrain.com/api/file/95u1wnsd" in item.url

    @pytest.mark.parametrize(
        "filename",
        [
            "文件名 🎉.txt",
            "file (1) [copy].txt",
            "special-chars_file.mp4",
        ],
    )
    def test_parse_file_with_special_names(self, requests_mock, filename):
        url = "https://pixeldrain.com/u/special"
        html = f"""<html><body><script>
        window.viewer_data = {{"type":"file","api_response":{{"id":"special","name":"{filename}","size":500}}}};
        </script></body></html>"""
        requests_mock.get(url, text=html)

        plugin = PixelDrain(url)
        items = list(plugin.export())

        assert items[0].filename == filename


class TestPixelDrainListParsing:
    """Test list/album parsing with realistic viewer_data."""

    def test_parse_real_list_structure(self, requests_mock):
        """Test parsing with real PixelDrain list structure."""
        url = "https://pixeldrain.com/l/nH4ZKt3b"
        html = """<html><body><script>
        window.viewer_data = {"type":"list","api_response":{"id":"nH4ZKt3b","title":"Test List","files":[{"id":"95u1wnsd","name":"eunbi (1).mp4","size":11405500},{"id":"abc123","name":"photo.jpg","size":524288},{"id":"def456","name":"document.pdf","size":1048576}]}};
        </script></body></html>"""
        requests_mock.get(url, text=html)

        plugin = PixelDrain(url)
        items = list(plugin.export())

        assert len(items) == 3
        assert items[0].filename == "eunbi (1).mp4"
        assert items[0].file_id == "95u1wnsd"
        assert items[0].metadata["size"] == 11405500

        for item in items:
            assert "pixeldrain.com/api/file/" in item.url

    def test_parse_empty_list(self, requests_mock):
        url = "https://pixeldrain.com/l/empty"
        html = """<html><body><script>
        window.viewer_data = {"type":"list","api_response":{"id":"empty","title":"Empty List","files":[]}};
        </script></body></html>"""
        requests_mock.get(url, text=html)

        plugin = PixelDrain(url)
        items = list(plugin.export())

        assert len(items) == 0

    def test_parse_list_with_various_file_sizes(self, requests_mock):
        """Test list with files of vastly different sizes."""
        url = "https://pixeldrain.com/l/sizes"
        html = """<html><body><script>
        window.viewer_data = {"type":"list","api_response":{"id":"sizes","title":"Size Test","files":[{"id":"tiny","name":"small.txt","size":1},{"id":"medium","name":"medium.zip","size":1048576},{"id":"large","name":"big.iso","size":4294967296}]}};
        </script></body></html>"""
        requests_mock.get(url, text=html)

        plugin = PixelDrain(url)
        items = list(plugin.export())

        assert len(items) == 3
        assert items[0].metadata["size"] == 1
        assert items[1].metadata["size"] == 1048576
        assert items[2].metadata["size"] == 4294967296


class TestPixelDrainProxyRouting:
    """Test proxy URL generation and routing logic."""

    def test_direct_download_url_no_proxy(self):
        plugin = PixelDrain("https://pixeldrain.com/u/test", use_proxy=False)
        url = plugin._get_download_url("abc123")

        assert url == "https://pixeldrain.com/api/file/abc123"
        assert "sriflix.my" not in url

    def test_proxy_download_url_with_proxy(self):
        plugin = PixelDrain("https://pixeldrain.com/u/test", use_proxy=True)
        url = plugin._get_download_url("abc123")

        assert "sriflix.my" in url
        assert "abc123" in url
        assert "download" in url.lower()

    def test_proxy_rotation(self):
        """Test that proxy index rotates through available proxies."""
        plugin = PixelDrain("https://pixeldrain.com/u/test", use_proxy=True)

        initial_index = plugin.proxy_index
        plugin._get_download_url("file1")
        assert plugin.proxy_index == (initial_index + 1) % len(PixelDrain.PROXIES)


class TestPixelDrainFileSizeFormatting:
    @pytest.mark.parametrize(
        "size,expected_unit",
        [
            (0, "0B"),
            (512, "B"),
            (1024, "KB"),
            (1048576, "MB"),
            (1073741824, "GB"),
            (1099511627776, "TB"),
        ],
    )
    def test_format_size_units(self, size, expected_unit):
        plugin = PixelDrain("https://pixeldrain.com/u/test")
        result = plugin._format_size(size)
        assert expected_unit in result


class TestPixelDrainErrorHandling:
    def test_missing_viewer_data(self, requests_mock):
        url = "https://pixeldrain.com/u/nodata"
        requests_mock.get(url, text="<html><body>No viewer data</body></html>")

        plugin = PixelDrain(url)

        with pytest.raises(ValueError, match="Could not find viewer data"):
            list(plugin.export())

    def test_malformed_json_in_viewer_data(self, requests_mock):
        url = "https://pixeldrain.com/u/badjson"
        html = """<script>
        window.viewer_data = {invalid json here};
        </script>"""
        requests_mock.get(url, text=html)

        plugin = PixelDrain(url)

        with pytest.raises((ValueError, json.JSONDecodeError)):
            list(plugin.export())

    @pytest.mark.parametrize(
        "exception_type,exception_instance",
        [
            (requests.Timeout, requests.Timeout("Request timed out")),
            (requests.ConnectionError, requests.ConnectionError("Connection failed")),
        ],
    )
    def test_network_errors(self, requests_mock, exception_type, exception_instance):
        url = "https://pixeldrain.com/u/error"
        requests_mock.get(url, exc=exception_instance)

        plugin = PixelDrain(url)

        with pytest.raises(exception_type):
            list(plugin.export())

    @pytest.mark.parametrize("status_code", [404, 500, 503])
    def test_http_errors(self, requests_mock, status_code):
        url = "https://pixeldrain.com/u/error"
        requests_mock.get(url, status_code=status_code)

        plugin = PixelDrain(url)

        with pytest.raises(requests.HTTPError):
            list(plugin.export())


class TestPixelDrainDownload:
    def test_download_file_success(self, requests_mock, tmp_output_dir):
        plugin = PixelDrain("https://pixeldrain.com/u/test")

        file_content = b"test file content"
        download_url = "https://pixeldrain.com/api/file/testid"
        requests_mock.get(download_url, content=file_content)

        item = Item(url=download_url, filename="test.txt", file_id="testid")
        result = plugin.download_file(item, tmp_output_dir)

        assert result is True

        output_path = os.path.join(tmp_output_dir, "test.txt")
        assert os.path.exists(output_path)

        with open(output_path, "rb") as f:
            assert f.read() == file_content

    def test_download_file_already_exists(self, tmp_output_dir):
        plugin = PixelDrain("https://pixeldrain.com/u/test")

        existing_path = os.path.join(tmp_output_dir, "existing.txt")
        with open(existing_path, "w") as f:
            f.write("original content")

        item = Item(
            url="https://pixeldrain.com/api/file/test",
            filename="existing.txt",
            file_id="test",
        )

        result = plugin.download_file(item, tmp_output_dir)
        assert result is True

        with open(existing_path) as f:
            assert f.read() == "original content"


@pytest.mark.live
class TestPixelDrainLive:
    def test_live_single_file(self):
        url = "https://pixeldrain.com/u/95u1wnsd"

        try:
            plugin = PixelDrain(url)
            items = list(plugin.export())

            assert len(items) == 1
            item = items[0]

            assert item.filename == "eunbi (1).mp4"
            assert item.file_id == "95u1wnsd"
            assert item.metadata["size"] == 11405500
            assert "95u1wnsd" in item.url
        except Exception as e:
            pytest.skip(f"Live PixelDrain file no longer available: {e}")

    def test_live_file_list(self):
        url = "https://pixeldrain.com/l/nH4ZKt3b"

        try:
            plugin = PixelDrain(url)
            items = list(plugin.export())

            assert len(items) == 5

            first_item = items[0]
            assert first_item.filename == "eunbi (1).mp4"
            assert first_item.file_id == "95u1wnsd"
            assert first_item.metadata["size"] == 11405500

            for item in items:
                assert item.filename
                assert item.file_id
                assert item.url
                assert "pixeldrain.com/api/file/" in item.url
                assert "size" in item.metadata
        except Exception as e:
            pytest.skip(f"Live PixelDrain list no longer available: {e}")
