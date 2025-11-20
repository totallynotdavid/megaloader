import pytest

from megaloader.plugins.cyberdrop import Cyberdrop

from tests.helpers import assert_valid_item
from tests.test_urls import CYBERDROP_URLS


@pytest.mark.live
def test_cyberdrop():
    """Test Cyberdrop extraction works."""
    url = CYBERDROP_URLS["images"]

    plugin = Cyberdrop(url)
    items = list(plugin.extract())

    # Basic assertions
    assert len(items) > 0, f"No items extracted from {url}"

    # Validate each item
    for item in items:
        assert_valid_item(item)
