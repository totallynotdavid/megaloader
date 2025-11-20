import pytest

from megaloader.plugins.thothub_vip import ThothubVIP

from tests.helpers import assert_valid_item
from tests.test_urls import THOTHUB_VIP_URLS


@pytest.mark.live
def test_thothub_vip_album():
    """Test Thothub.vip album extraction."""
    url = THOTHUB_VIP_URLS["album"]

    plugin = ThothubVIP(url)
    items = list(plugin.extract())

    assert len(items) > 0, f"No items extracted from {url}"

    for item in items:
        assert_valid_item(item)


@pytest.mark.live
def test_thothub_vip_single_video():
    """Test Thothub.vip single video extraction."""
    url = THOTHUB_VIP_URLS["single_video"]

    plugin = ThothubVIP(url)
    items = list(plugin.extract())

    assert len(items) == 1, (
        f"Expected exactly 1 item from single video URL, got {len(items)}"
    )
    assert_valid_item(items[0])
