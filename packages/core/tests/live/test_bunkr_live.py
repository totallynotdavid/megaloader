import pytest
import requests

from megaloader.plugins.bunkr import Bunkr

from tests.helpers import check_url_accessible, format_failure_message, validate_item
from tests.test_urls import BUNKR_URLS


@pytest.mark.live
class TestBunkrLive:
    """Test Bunkr plugin against real site."""

    def test_album_extraction_images(self):
        """
        Test extracting image album from Bunkr.
        Catches: HTML structure changes, download link changes.
        """
        url = BUNKR_URLS["images"]

        try:
            plugin = Bunkr(url)
            items = list(plugin.extract())

            # Validate we got items
            assert len(items) == 6, f"Expected 6 items, got {len(items)}"

            # Validate each item
            all_issues = []
            for i, item in enumerate(items):
                issues = validate_item(item, "Bunkr")
                if issues:
                    all_issues.append(f"Item {i}: " + ", ".join(issues))

                # Specific for this album
                if not item.filename.startswith(
                    "sample-image-"
                ) or not item.filename.endswith(".jpg"):
                    all_issues.append(f"Unexpected filename: {item.filename}")

            # Check if at least first download URL works
            if items:
                is_accessible, status = check_url_accessible(items[0].download_url)
                if not is_accessible:
                    all_issues.append(f"Download URL not accessible: {status}")

            # Assert with detailed message
            if all_issues:
                pytest.fail(
                    format_failure_message(
                        "Bunkr",
                        url,
                        items,
                        expected_min=6,
                        issues=all_issues,
                    )
                )

        except requests.RequestException as e:
            pytest.skip(f"Network error (retry later): {e}")

    def test_album_extraction_videos(self):
        """
        Test extracting video album from Bunkr.
        Catches: Video-specific extraction issues.
        """
        url = BUNKR_URLS["videos"]

        try:
            plugin = Bunkr(url)
            items = list(plugin.extract())

            assert len(items) > 0, f"No items extracted from {url}"

            all_issues = []
            for i, item in enumerate(items):
                issues = validate_item(item, "Bunkr")
                if issues:
                    all_issues.append(f"Item {i}: " + ", ".join(issues))

                # Videos should have video extensions
                if item.filename and not any(
                    item.filename.lower().endswith(ext)
                    for ext in [".mp4", ".webm", ".mkv", ".mov", ".avi"]
                ):
                    all_issues.append(
                        f"Video item has non-video extension: {item.filename}"
                    )

            if all_issues:
                pytest.fail(
                    format_failure_message(
                        "Bunkr",
                        url,
                        items,
                        expected_min=1,
                        issues=all_issues,
                    )
                )

        except requests.RequestException as e:
            pytest.skip(f"Network error: {e}")

    def test_single_file_extraction(self):
        """
        Test extracting single file from Bunkr.
        Catches: Single file vs album handling.
        """
        url = BUNKR_URLS["single_file"]

        try:
            plugin = Bunkr(url)
            items = list(plugin.extract())

            # Should return exactly 1 item
            assert len(items) == 1, f"Expected 1 item, got {len(items)}"

            all_issues = []
            issues = validate_item(items[0], "Bunkr")
            if issues:
                all_issues.extend(issues)

            if all_issues:
                pytest.fail(
                    format_failure_message(
                        "Bunkr",
                        url,
                        items,
                        expected_min=1,
                        issues=all_issues,
                    )
                )

        except requests.RequestException as e:
            pytest.skip(f"Network error: {e}")
