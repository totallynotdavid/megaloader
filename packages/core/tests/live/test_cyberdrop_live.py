import pytest

from megaloader.plugins.cyberdrop import Cyberdrop

from tests.helpers import assert_valid_item
from tests.test_urls import CYBERDROP_URLS


@pytest.mark.live
def test_cyberdrop_album_images():
    """Test Cyberdrop album extraction with images."""
    url = CYBERDROP_URLS["images"]

    plugin = Cyberdrop(url)
    items = list(plugin.extract())

    assert len(items) > 0, f"No items extracted from {url}"

    for item in items:
        assert_valid_item(item)


@pytest.mark.live
def test_cyberdrop_album_videos():
    url = CYBERDROP_URLS["videos"]

    plugin = Cyberdrop(url)
    items = list(plugin.extract())

    assert len(items) > 0, f"No items extracted from {url}"

    for item in items:
        assert_valid_item(item)


@pytest.mark.live
def test_cyberdrop_single_file():
    url = CYBERDROP_URLS["single_file"]

    plugin = Cyberdrop(url)
    items = list(plugin.extract())

    assert len(items) == 1, (
        f"Expected exactly 1 item from single file URL, got {len(items)}"
    )
    assert_valid_item(items[0])
