import os
import tempfile

import pytest

from megaloader.http import download_file


@pytest.mark.unit
class TestDownloadFileUtility:
    def test_filename_extraction_from_url(self, requests_mock):
        """Test filename parsing from various URL formats"""
        test_cases = [
            ("https://example.com/file.txt", "file.txt"),
            (
                "https://example.com/path/file%20with%20spaces.jpg",
                "file with spaces.jpg",
            ),
            ("https://example.com/file", "file"),
            ("https://example.com/", None),  # No filename
        ]

        for url, expected in test_cases:
            requests_mock.get(url, content=b"test")
            result = download_file(url, tempfile.gettempdir())
            if expected:
                assert result is not None
                assert os.path.basename(result) == expected
            else:
                assert result is None

    def test_sanitizes_filenames(self, requests_mock, tmp_path):
        dangerous_urls = [
            ("https://example.com/path/file.txt", "file.txt"),  # / becomes _
            ("https://example.com/path\\file.txt", "file.txt"),  # \ handled by basename
        ]

        for url, expected_filename in dangerous_urls:
            requests_mock.get(url, content=b"test")
            result = download_file(url, str(tmp_path))
            assert result is not None
            assert os.path.basename(result) == expected_filename

    def test_creates_output_directory(self, requests_mock, tmp_path):
        """Test that missing output directories are created"""
        nested_dir = tmp_path / "deep" / "nested" / "path"
        assert not nested_dir.exists()

        url = "https://example.com/test.txt"
        requests_mock.get(url, content=b"content")

        result = download_file(url, str(nested_dir))
        assert result is not None
        assert nested_dir.exists()
        assert os.path.exists(result)

    def test_handles_network_errors(self, requests_mock, tmp_path):
        import requests

        url = "https://example.com/fail.txt"

        # Test 404
        requests_mock.get(url, status_code=404)
        result = download_file(url, str(tmp_path))
        assert result is None

        # Test connection timeout
        requests_mock.get(url, exc=requests.exceptions.ConnectTimeout)
        result = download_file(url, str(tmp_path))
        assert result is None

    def test_skips_existing_files(self, requests_mock, tmp_path):
        """Test that existing files are not re-downloaded"""
        url = "https://example.com/existing.txt"
        file_path = tmp_path / "existing.txt"

        # Create existing file with content
        file_path.write_text("existing content")

        # Mock request that should not be called
        requests_mock.get(url, content=b"new content")

        result = download_file(url, str(tmp_path))
        assert result == str(file_path)
        # File should still have original content
        assert file_path.read_text() == "existing content"

    def test_custom_headers(self, requests_mock, tmp_path):
        url = "https://example.com/custom.txt"
        custom_headers = {"X-Custom": "test"}

        # Mock to verify headers
        def match_headers(request):
            return request.headers.get("X-Custom") == "test"

        requests_mock.get(url, content=b"test", additional_matcher=match_headers)

        result = download_file(url, str(tmp_path), headers=custom_headers)
        assert result is not None
