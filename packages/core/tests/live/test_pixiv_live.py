import pytest

from megaloader.plugins.pixiv import Pixiv

from tests.helpers import assert_valid_item
from tests.test_urls import PIXIV_URLS


@pytest.mark.live
def test_pixiv_artwork():
    """Test Pixiv artwork extraction."""
    url = PIXIV_URLS["artwork"]

    plugin = Pixiv(url)
    items = list(plugin.extract())

    assert len(items) > 0, f"No items extracted from {url}"

    for item in items:
        assert_valid_item(item)
