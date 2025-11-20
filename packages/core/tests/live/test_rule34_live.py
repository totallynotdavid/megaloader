import os

import pytest

from megaloader.plugins.rule34 import Rule34

from tests.helpers import assert_valid_item
from tests.test_urls import RULE34_URLS


@pytest.mark.live
def test_rule34_tags_scraping():
    """Test Rule34 tags search using scraping mode (no auth)."""
    url = RULE34_URLS["tags"]

    plugin = Rule34(url)
    items = list(plugin.extract())

    assert len(items) > 0, f"No items extracted from {url}"

    for item in items:
        assert_valid_item(item)


@pytest.mark.live
def test_rule34_single_post():
    """Test Rule34 single post extraction."""
    url = RULE34_URLS["single_post"]

    plugin = Rule34(url)
    items = list(plugin.extract())

    assert len(items) == 1, (
        f"Expected exactly 1 item from single post URL, got {len(items)}"
    )
    assert_valid_item(items[0])


@pytest.mark.live
def test_rule34_tags_api():
    """Test Rule34 tags search using API mode (requires credentials)."""
    api_key = os.getenv("RULE34_API_KEY")
    user_id = os.getenv("RULE34_USER_ID")

    if not api_key or not user_id:
        pytest.skip("RULE34_API_KEY and RULE34_USER_ID not set")

    url = RULE34_URLS["tags"]

    plugin = Rule34(url, api_key=api_key, user_id=user_id)
    items = list(plugin.extract())

    assert len(items) > 0, f"No items extracted from {url}"

    for item in items:
        assert_valid_item(item)
