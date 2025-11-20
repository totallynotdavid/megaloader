import pytest

from megaloader.plugins.thothub_to import ThothubTO

from tests.helpers import assert_valid_item
from tests.test_urls import THOTHUB_TO_URLS


@pytest.mark.live
def test_thothub_to_model():
    url = THOTHUB_TO_URLS["model"]

    plugin = ThothubTO(url)
    items = list(plugin.extract())

    assert len(items) > 0, f"No items extracted from {url}"

    for item in items:
        assert_valid_item(item)


@pytest.mark.live
def test_thothub_to_album():
    url = THOTHUB_TO_URLS["album"]

    plugin = ThothubTO(url)
    items = list(plugin.extract())

    assert len(items) > 0, f"No items extracted from {url}"

    for item in items:
        assert_valid_item(item)


@pytest.mark.live
def test_thothub_to_single_video():
    url = THOTHUB_TO_URLS["single_video"]

    plugin = ThothubTO(url)
    items = list(plugin.extract())

    assert len(items) == 1, (
        f"Expected exactly 1 item from single video URL, got {len(items)}"
    )
    assert_valid_item(items[0])
