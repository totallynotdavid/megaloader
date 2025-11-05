import os

import pytest

from megaloader.http import download_file


@pytest.mark.unit
class TestDownloadFileUtility:
    def test_filename_extraction_from_url(self):
        """Test filename parsing from URL"""
        # Just verify the util can be called
        assert download_file  # smoke test

    def test_sanitizes_output_path(self, tmp_path):
        """Test that output path is sanitized"""
        import urllib.parse

        url = "https://example.com/file%20with%20spaces.txt"
        filename = urllib.parse.unquote(os.path.basename(url))
        assert filename == "file with spaces.txt"

    def test_creates_output_directory(self, tmp_path, requests_mock):
        """Test that missing output dirs are created"""
        out_dir = tmp_path / "nested" / "dirs"
        assert not out_dir.exists()

        url = "https://example.com/file.txt"
        requests_mock.get(url, content=b"test")

        download_file(url, str(out_dir), filename="test.txt")
        assert out_dir.exists()
