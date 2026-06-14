import pytest

from megaloader import extract
from syrupy.assertion import SnapshotAssertion

from tests.helpers import assert_valid_item
from tests.plugins.normalize import normalize_items
from tests.test_urls import RULE34_URLS


@pytest.mark.vcr
def test_rule34_tags_scraping(snapshot: SnapshotAssertion) -> None:
    items = list(extract(RULE34_URLS["tags"]))

    assert items
    for item in items:
        assert_valid_item(item)
    assert normalize_items(items) == snapshot


@pytest.mark.vcr
def test_rule34_single_post(snapshot: SnapshotAssertion) -> None:
    items = list(extract(RULE34_URLS["single_post"]))

    assert len(items) == 1
    assert_valid_item(items[0])
    assert normalize_items(items) == snapshot
