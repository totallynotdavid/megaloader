import pytest

from megaloader.plugins.bunkr import Bunkr

from tests.helpers import assert_valid_item
from tests.test_urls import BUNKR_URLS


@pytest.mark.live
def test_bunkr_album_images():
    """Test Bunkr album extraction with images."""
    url = BUNKR_URLS["images"]

    plugin = Bunkr(url)
    items = list(plugin.extract())

    assert len(items) > 0, f"No items extracted from {url}"

    for item in items:
        assert_valid_item(item)


@pytest.mark.live
def test_bunkr_album_videos():
    """Test Bunkr album extraction with videos."""
    url = BUNKR_URLS["videos"]

    plugin = Bunkr(url)
    items = list(plugin.extract())

    assert len(items) > 0, f"No items extracted from {url}"

    for item in items:
        assert_valid_item(item)


@pytest.mark.live
def test_bunkr_single_file():
    """Test Bunkr single file extraction."""
    url = BUNKR_URLS["single_file"]

    plugin = Bunkr(url)
    items = list(plugin.extract())

    assert len(items) == 1, (
        f"Expected exactly 1 item from single file URL, got {len(items)}"
    )
    assert_valid_item(items[0])
