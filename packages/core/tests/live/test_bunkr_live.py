import pytest

from megaloader.plugins.bunkr import Bunkr

from tests.helpers import assert_valid_item
from tests.test_urls import BUNKR_URLS


@pytest.mark.live
def test_bunkr():
    """Test Bunkr extraction works."""
    url = BUNKR_URLS["images"]

    plugin = Bunkr(url)
    items = list(plugin.extract())

    # Basic assertions
    assert len(items) > 0, f"No items extracted from {url}"

    # Validate each item
    for item in items:
        assert_valid_item(item)
