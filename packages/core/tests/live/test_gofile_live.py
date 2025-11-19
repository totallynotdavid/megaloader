import pytest
import requests

from megaloader.plugins.gofile import Gofile

from tests.helpers import format_failure_message, validate_item
from tests.test_urls import GOFILE_URLS


@pytest.mark.live
class TestGofileLive:
    """Test Gofile plugin against real site."""

    def test_token_acquisition(self) -> None:
        """
        CRITICAL: Test that Gofile authentication flow works.
        Catches: Token endpoint changes, JS variable changes.
        """
        try:
            plugin = Gofile("https://gofile.io/d/test")

            # These should not raise
            website_token = plugin._get_website_token()
            api_token = plugin._create_account()

            assert website_token, "Failed to get website token"
            assert api_token, "Failed to create guest account"
            assert len(website_token) > 10, (
                f"Suspicious website token length: {len(website_token)}"
            )
            assert len(api_token) > 10, f"Suspicious API token length: {len(api_token)}"

        except Exception as e:
            pytest.fail(
                f"Gofile authentication FAILED:\n"
                f"Error: {e}\n"
                f"This likely means Gofile changed their auth flow.\n"
                f"Check _get_website_token() and _create_account() methods."
            )

    def test_folder_extraction_images(self) -> None:
        """
        Test extracting image folder from Gofile.
        Catches: API response changes, file listing changes.
        """
        url = GOFILE_URLS["images"]

        try:
            plugin = Gofile(url)
            items = list(plugin.extract())

            assert len(items) > 0, f"No items extracted from {url}"

            all_issues = []
            for i, item in enumerate(items):
                issues = validate_item(item, "Gofile")
                if issues:
                    all_issues.append(f"Item {i}: " + ", ".join(issues))

                # Gofile should provide size_bytes
                if item.size_bytes is None:
                    all_issues.append(
                        f"Item {i} missing size_bytes (API may have changed)"
                    )

            if all_issues:
                pytest.fail(
                    format_failure_message(
                        "Gofile",
                        url,
                        items,
                        expected_min=1,
                        issues=all_issues,
                    )
                )

        except requests.RequestException as e:
            pytest.skip(f"Network error: {e}")

    def test_folder_extraction_videos(self) -> None:
        """Test extracting video folder from Gofile."""
        url = GOFILE_URLS["videos"]

        try:
            plugin = Gofile(url)
            items = list(plugin.extract())

            assert len(items) > 0, f"No items extracted from {url}"

            all_issues = []
            for i, item in enumerate(items):
                issues = validate_item(item, "Gofile")
                if issues:
                    all_issues.append(f"Item {i}: " + ", ".join(issues))

            if all_issues:
                pytest.fail(
                    format_failure_message(
                        "Gofile",
                        url,
                        items,
                        expected_min=1,
                        issues=all_issues,
                    )
                )

        except requests.RequestException as e:
            pytest.skip(f"Network error: {e}")
