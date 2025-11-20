import pytest

from megaloader.plugins.pixeldrain import PixelDrain

from tests.helpers import assert_valid_item
from tests.test_urls import PIXELDRAIN_URLS


@pytest.mark.live
def test_pixeldrain_list_images():
    """Test PixelDrain list extraction with images."""
    url = PIXELDRAIN_URLS["images"]

    plugin = PixelDrain(url)
    items = list(plugin.extract())

    assert len(items) > 0, f"No items extracted from {url}"

    for item in items:
        assert_valid_item(item)


@pytest.mark.live
def test_pixeldrain_list_videos():
    """Test PixelDrain list extraction with videos."""
    url = PIXELDRAIN_URLS["videos"]

    plugin = PixelDrain(url)
    items = list(plugin.extract())

    assert len(items) > 0, f"No items extracted from {url}"

    for item in items:
        assert_valid_item(item)


@pytest.mark.live
def test_pixeldrain_single_file():
    """Test PixelDrain single file extraction."""
    url = PIXELDRAIN_URLS["single_file"]

    plugin = PixelDrain(url)
    items = list(plugin.extract())

    assert len(items) == 1, (
        f"Expected exactly 1 item from single file URL, got {len(items)}"
    )
    assert_valid_item(items[0])
