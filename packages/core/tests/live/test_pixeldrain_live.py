import pytest

from megaloader.plugins.pixeldrain import PixelDrain

from tests.helpers import assert_valid_item
from tests.test_urls import PIXELDRAIN_URLS


@pytest.mark.live
def test_pixeldrain():
    """Test PixelDrain extraction works."""
    url = PIXELDRAIN_URLS["images"]

    plugin = PixelDrain(url)
    items = list(plugin.extract())

    # Basic assertions
    assert len(items) > 0, f"No items extracted from {url}"

    # Validate each item
    for item in items:
        assert_valid_item(item)
