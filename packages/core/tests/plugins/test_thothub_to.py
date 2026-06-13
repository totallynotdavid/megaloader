import pytest

from megaloader import extract
from syrupy.assertion import SnapshotAssertion

from tests.helpers import assert_valid_item
from tests.plugins.normalize import normalize_items
from tests.test_urls import THOTHUB_TO_URLS


@pytest.mark.vcr
def test_thothub_to_album(snapshot: SnapshotAssertion) -> None:
    items = list(extract(THOTHUB_TO_URLS["album"]))

    assert items
    for item in items:
        assert_valid_item(item)
    assert normalize_items(items) == snapshot


@pytest.mark.vcr
def test_thothub_to_single_video(snapshot: SnapshotAssertion) -> None:
    items = list(extract(THOTHUB_TO_URLS["single_video"]))

    assert len(items) == 1
    assert_valid_item(items[0])
    assert normalize_items(items) == snapshot
