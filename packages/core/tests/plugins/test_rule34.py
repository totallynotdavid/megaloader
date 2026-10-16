import pytest

from megaloader import extract
from syrupy.assertion import SnapshotAssertion

from tests.plugins.normalize import normalize_items
from tests.test_urls import RULE34_URLS


@pytest.mark.vcr
def test_rule34_tags_scraping(snapshot: SnapshotAssertion) -> None:
    items = list(extract(RULE34_URLS["tags"]))

    assert items
    assert normalize_items(items) == snapshot


@pytest.mark.vcr
def test_rule34_single_post(snapshot: SnapshotAssertion) -> None:
    items = list(extract(RULE34_URLS["single_post"]))

    assert len(items) == 1
    assert normalize_items(items) == snapshot
