import pytest
import requests

from megaloader.plugins.pixeldrain import PixelDrain

from tests.helpers import format_failure_message, validate_item
from tests.test_urls import PIXELDRAIN_URLS


@pytest.mark.live
class TestPixelDrainLive:
    """Test PixelDrain plugin against real site."""

    def test_viewer_data_structure(self) -> None:
        """
        CRITICAL: Test that window.viewer_data still exists and is parseable.
        Catches: Page structure changes, JS variable renames.
        """
        url = PIXELDRAIN_URLS["images"]

        try:
            import json
            import re

            plugin = PixelDrain(url)
            response = plugin.session.get(url, timeout=30)
            response.raise_for_status()

            # Check if viewer_data exists
            match = re.search(
                r"window\.viewer_data\s*=\s*({.*?});",
                response.text,
                re.DOTALL,
            )

            assert match, (
                "Could not find window.viewer_data in page\n"
                "PixelDrain may have changed their page structure"
            )

            # Check if it's valid JSON
            try:
                data = json.loads(match.group(1))
            except json.JSONDecodeError as e:
                pytest.fail(f"window.viewer_data is not valid JSON: {e}")

            # Check expected structure
            assert "api_response" in data, (
                "window.viewer_data missing 'api_response' key"
            )

        except requests.RequestException as e:
            pytest.skip(f"Network error: {e}")

    def test_list_extraction_images(self) -> None:
        """
        Test extracting image list from PixelDrain.
        Catches: List format changes, metadata changes.
        """
        url = PIXELDRAIN_URLS["images"]

        try:
            plugin = PixelDrain(url)
            items = list(plugin.extract())

            assert len(items) == 6, f"Expected 6 items, got {len(items)}"

            all_issues = []
            for i, item in enumerate(items):
                issues = validate_item(item, "PixelDrain")
                if issues:
                    all_issues.append(f"Item {i}: " + ", ".join(issues))

                # PixelDrain should provide size_bytes
                if item.size_bytes is None:
                    all_issues.append(f"Item {i} missing size_bytes")

                # Download URLs should be API format
                if not item.download_url.startswith("https://pixeldrain.com/api/file/"):
                    all_issues.append(
                        f"Item {i} has unexpected URL format: {item.download_url}"
                    )

                # Specific assertions for this album
                expected_sizes = {89101, 202748, 207558, 286359, 405661, 412156}
                if item.size_bytes not in expected_sizes:
                    all_issues.append(f"Unexpected size: {item.size_bytes}")

                if not item.filename.startswith(
                    "sample-image-"
                ) or not item.filename.endswith(".jpg"):
                    all_issues.append(f"Unexpected filename: {item.filename}")

            if all_issues:
                pytest.fail(
                    format_failure_message(
                        "PixelDrain",
                        url,
                        items,
                        expected_min=6,
                        issues=all_issues,
                    )
                )

        except requests.RequestException as e:
            pytest.skip(f"Network error: {e}")

    def test_list_extraction_videos(self) -> None:
        """Test extracting video list from PixelDrain."""
        url = PIXELDRAIN_URLS["videos"]

        try:
            plugin = PixelDrain(url)
            items = list(plugin.extract())

            assert len(items) == 4, f"Expected 4 items, got {len(items)}"

            all_issues = []
            for i, item in enumerate(items):
                issues = validate_item(item, "PixelDrain")
                if issues:
                    all_issues.append(f"Item {i}: " + ", ".join(issues))

                # Specific for videos
                expected_sizes = {1575527, 2247200, 5207169, 5243523}
                if item.size_bytes not in expected_sizes:
                    all_issues.append(f"Unexpected size: {item.size_bytes}")

                if not item.filename.startswith("sample-video-"):
                    all_issues.append(f"Unexpected filename: {item.filename}")

                video_exts = {".webm", ".mkv", ".mov", ".mp4"}
                if not any(item.filename.endswith(ext) for ext in video_exts):
                    all_issues.append(f"Non-video extension: {item.filename}")

            if all_issues:
                pytest.fail(
                    format_failure_message(
                        "PixelDrain",
                        url,
                        items,
                        expected_min=4,
                        issues=all_issues,
                    )
                )

        except requests.RequestException as e:
            pytest.skip(f"Network error: {e}")

    def test_single_file_extraction(self) -> None:
        """
        Test extracting single file from PixelDrain.
        Catches: Single file vs list handling.
        """
        url = PIXELDRAIN_URLS["single_file"]

        try:
            plugin = PixelDrain(url)
            items = list(plugin.extract())

            # Should return exactly 1 item
            assert len(items) == 1, f"Expected 1 item, got {len(items)}"

            all_issues = []
            issues = validate_item(items[0], "PixelDrain")
            if issues:
                all_issues.extend(issues)

            if all_issues:
                pytest.fail(
                    format_failure_message(
                        "PixelDrain",
                        url,
                        items,
                        expected_min=1,
                        issues=all_issues,
                    )
                )

        except requests.RequestException as e:
            pytest.skip(f"Network error: {e}")
