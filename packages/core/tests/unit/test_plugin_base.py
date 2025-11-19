import pytest

from megaloader.item import DownloadItem


@pytest.mark.unit
class TestBasePluginContract:
    def test_item_dataclass_required_fields(self) -> None:
        """Verify DownloadItem requires download_url and filename."""
        item = DownloadItem(
            download_url="http://example.com/file.txt", filename="test.txt"
        )
        assert item.download_url == "http://example.com/file.txt"
        assert item.filename == "test.txt"
        assert item.collection_name is None
        assert item.source_id is None
        assert item.headers == {}
        assert item.size_bytes is None

    def test_item_dataclass_optional_fields(self) -> None:
        """Verify DownloadItem optional fields work correctly."""
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

    def test_item_rejects_empty_download_url(self) -> None:
        """DownloadItem should reject empty download_url."""
        with pytest.raises(ValueError, match="download_url cannot be empty"):
            DownloadItem(download_url="", filename="test.txt")

    def test_item_rejects_empty_filename(self) -> None:
        """DownloadItem should reject empty filename."""
        with pytest.raises(ValueError, match="filename cannot be empty"):
            DownloadItem(download_url="http://example.com/file", filename="")

    def test_plugin_registry_has_all_domains(self) -> None:
        """Verify all expected domains are registered."""
        from megaloader.plugins import PLUGIN_REGISTRY

        expected_domains = [
            "bunkr.si",
            "bunkr.la",
            "bunkr.is",
            "bunkr.ru",
            "bunkr.su",
            "cyberdrop.me",
            "cyberdrop.to",
            "fanbox.cc",
            "fapello.com",
            "gofile.io",
            "pixeldrain.com",
            "pixiv.net",
            "rule34.xxx",
            "thothub.to",
            "thothub.vip",
            "thotslife.com",
        ]

        for domain in expected_domains:
            assert domain in PLUGIN_REGISTRY, (
                f"Domain '{domain}' missing from PLUGIN_REGISTRY"
            )

    def test_subdomain_support_configured(self) -> None:
        """Verify subdomain support is configured."""
        from megaloader.plugins import SUBDOMAIN_SUPPORTED

        assert "fanbox.cc" in SUBDOMAIN_SUPPORTED
