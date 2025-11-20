import pytest

from megaloader.plugins.fanbox import Fanbox

from tests.helpers import assert_valid_item
from tests.test_urls import FANBOX_URLS


@pytest.mark.live
def test_fanbox_creator():
    url = FANBOX_URLS["creator"]

    plugin = Fanbox(url)
    items = list(plugin.extract())

    assert len(items) > 0, f"No items extracted from {url}"

    for item in items:
        assert_valid_item(item)
