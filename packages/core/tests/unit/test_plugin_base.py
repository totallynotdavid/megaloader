import pytest
import requests
import requests_mock as req_mock

from megaloader.exceptions import ExtractionError
from megaloader.item import DownloadItem
from megaloader.plugin import BasePlugin


class DummyPlugin(BasePlugin):
    def extract(self):
        yield DownloadItem(
            download_url="https://example.com/file.txt",
            filename="file.txt",
        )


@pytest.mark.unit
class TestDownloadItem:
    def test_required_fields(self) -> None:
        item = DownloadItem(
            download_url="http://example.com/file.txt", filename="test.txt"
        )

        assert item.download_url == "http://example.com/file.txt"
        assert item.filename == "test.txt"
        assert item.collection_name is None
        assert item.source_id is None
        assert item.headers == {}
        assert item.size_bytes is None

    def test_optional_fields(self) -> None:
        headers = {"Referer": "http://example.com"}
        item = DownloadItem(
            download_url="http://example.com/file.txt",
            filename="test.txt",
            collection_name="Test Album",
            source_id="12345",
            headers=headers,
            size_bytes=1024,
        )

        assert item.collection_name == "Test Album"
        assert item.source_id == "12345"
        assert item.headers == headers
        assert item.size_bytes == 1024

    def test_rejects_empty_download_url(self) -> None:
        with pytest.raises(ValueError, match="download_url cannot be empty"):
            DownloadItem(download_url="", filename="test.txt")

    def test_rejects_empty_filename(self) -> None:
        with pytest.raises(ValueError, match="filename cannot be empty"):
            DownloadItem(download_url="http://example.com/file", filename="")

    def test_rejects_filename_with_path_separator(self) -> None:
        with pytest.raises(ValueError, match="leaf name"):
            DownloadItem(
                download_url="http://example.com/file",
                filename="folder/file.txt",
            )

    def test_rejects_path_traversal(self) -> None:
        with pytest.raises(ValueError, match="path traversal"):
            DownloadItem(
                download_url="http://example.com/file",
                filename="..file.txt",
            )


@pytest.mark.unit
class TestBasePluginRequest:
    def _plugin(self) -> DummyPlugin:
        return DummyPlugin("https://example.com/file.txt")

    def test_get_returns_response_on_success(self, requests_mock: req_mock.Mocker) -> None:
        requests_mock.get("https://example.com/data", text="ok")
        plugin = self._plugin()
        response = plugin._get("https://example.com/data")
        assert response.text == "ok"

    def test_get_maps_http_error_to_extraction_error(self, requests_mock: req_mock.Mocker) -> None:
        requests_mock.get("https://example.com/data", status_code=404)
        plugin = self._plugin()

        with pytest.raises(ExtractionError) as exc_info:
            plugin._get("https://example.com/data")

        err = exc_info.value
        assert err.http_status == 404
        assert err.category == "access"
        assert err.source == "dummyplugin"

    def test_get_classifies_rate_limit(self, requests_mock: req_mock.Mocker) -> None:
        requests_mock.get("https://example.com/data", status_code=429)
        plugin = self._plugin()

        with pytest.raises(ExtractionError) as exc_info:
            plugin._get("https://example.com/data")

        assert exc_info.value.category == "rate_limit"
        assert exc_info.value.http_status == 429

    def test_get_classifies_auth_error(self, requests_mock: req_mock.Mocker) -> None:
        requests_mock.get("https://example.com/data", status_code=401)
        plugin = self._plugin()

        with pytest.raises(ExtractionError) as exc_info:
            plugin._get("https://example.com/data")

        assert exc_info.value.category == "auth"

    def test_get_maps_connection_error_to_extraction_error(self, requests_mock: req_mock.Mocker) -> None:
        requests_mock.get("https://example.com/data", exc=requests.ConnectionError("refused"))
        plugin = self._plugin()

        with pytest.raises(ExtractionError) as exc_info:
            plugin._get("https://example.com/data")

        assert exc_info.value.category == "network"

    def test_get_maps_timeout_to_extraction_error(self, requests_mock: req_mock.Mocker) -> None:
        requests_mock.get("https://example.com/data", exc=requests.Timeout("timed out"))
        plugin = self._plugin()

        with pytest.raises(ExtractionError) as exc_info:
            plugin._get("https://example.com/data")

        assert exc_info.value.category == "timeout"

    def test_post_returns_response_on_success(self, requests_mock: req_mock.Mocker) -> None:
        requests_mock.post("https://example.com/api", json={"status": "ok"})
        plugin = self._plugin()
        response = plugin._post("https://example.com/api")
        assert response.json() == {"status": "ok"}

    def test_post_maps_http_error_to_extraction_error(self, requests_mock: req_mock.Mocker) -> None:
        requests_mock.post("https://example.com/api", status_code=403)
        plugin = self._plugin()

        with pytest.raises(ExtractionError) as exc_info:
            plugin._post("https://example.com/api")

        assert exc_info.value.http_status == 403
        assert exc_info.value.category == "access"

    def test_extraction_error_preserves_cause(self, requests_mock: req_mock.Mocker) -> None:
        requests_mock.get("https://example.com/data", status_code=500)
        plugin = self._plugin()

        with pytest.raises(ExtractionError) as exc_info:
            plugin._get("https://example.com/data")

        assert exc_info.value.__cause__ is not None
        assert isinstance(exc_info.value.__cause__, requests.HTTPError)
