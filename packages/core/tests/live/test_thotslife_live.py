import pytest

from megaloader.plugins.thotslife import Thotslife

from tests.helpers import assert_valid_item
from tests.test_urls import THOTSLIFE_URLS


@pytest.mark.live
def test_thotslife_post():
    url = THOTSLIFE_URLS["post"]

    plugin = Thotslife(url)
    items = list(plugin.extract())

    assert len(items) > 0, f"No items extracted from {url}"

    for item in items:
        assert_valid_item(item)
