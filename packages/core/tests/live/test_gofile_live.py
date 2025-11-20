import pytest

from megaloader.plugins.gofile import Gofile

from tests.helpers import assert_valid_item
from tests.test_urls import GOFILE_URLS


@pytest.mark.live
def test_gofile():
    """Test Gofile extraction works."""
    url = GOFILE_URLS["images"]

    plugin = Gofile(url)
    items = list(plugin.extract())

    # Basic assertions
    assert len(items) > 0, f"No items extracted from {url}"

    # Validate each item
    for item in items:
        assert_valid_item(item)
