import pytest
import requests

from megaloader.plugins.cyberdrop import Cyberdrop

from tests.helpers import format_failure_message, validate_item
from tests.test_urls import CYBERDROP_URLS


@pytest.mark.live
class TestCyberdropLive:
    """Test Cyberdrop plugin against real site."""

    def test_album_extraction_images(self):
        """
        Test extracting image album from Cyberdrop.
        Catches: HTML structure changes, API changes.
        """
        url = CYBERDROP_URLS["images"]

        try:
            plugin = Cyberdrop(url)
            items = list(plugin.extract())

            assert len(items) > 0, f"No items extracted from {url}"

            all_issues = []
            for i, item in enumerate(items):
                issues = validate_item(item, "Cyberdrop")
                if issues:
                    all_issues.append(f"Item {i}: " + ", ".join(issues))

                # Cyberdrop uses API - should have auth_url
                if not item.download_url.startswith("https://"):
                    all_issues.append(f"Invalid download URL: {item.download_url}")

            if all_issues:
                pytest.fail(
                    format_failure_message(
                        "Cyberdrop",
                        url,
                        items,
                        expected_min=1,
                        issues=all_issues,
                    )
                )

        except requests.RequestException as e:
            pytest.skip(f"Network error: {e}")

    def test_album_extraction_videos(self):
        """Test extracting video album from Cyberdrop."""
        url = CYBERDROP_URLS["videos"]

        try:
            plugin = Cyberdrop(url)
            items = list(plugin.extract())

            assert len(items) > 0, f"No items extracted from {url}"

            all_issues = []
            for i, item in enumerate(items):
                issues = validate_item(item, "Cyberdrop")
                if issues:
                    all_issues.append(f"Item {i}: " + ", ".join(issues))

            if all_issues:
                pytest.fail(
                    format_failure_message(
                        "Cyberdrop",
                        url,
                        items,
                        expected_min=1,
                        issues=all_issues,
                    )
                )

        except requests.RequestException as e:
            pytest.skip(f"Network error: {e}")

    def test_album_title_extracted(self):
        """
        Test that album title is extracted as collection_name.
        Catches: Title extraction breaking.
        """
        url = CYBERDROP_URLS["images"]

        try:
            plugin = Cyberdrop(url)
            items = list(plugin.extract())

            assert len(items) > 0

            # At least some items should have collection_name
            with_collection = [item for item in items if item.collection_name]

            assert len(with_collection) > 0, (
                "No items have collection_name - album title extraction may be broken"
            )

        except requests.RequestException as e:
            pytest.skip(f"Network error: {e}")
