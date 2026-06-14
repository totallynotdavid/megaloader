import pytest

from megaloader import extract
from syrupy.assertion import SnapshotAssertion

from tests.helpers import assert_valid_item
from tests.plugins.normalize import normalize_items
from tests.test_urls import CYBERDROP_URLS


@pytest.mark.vcr
def test_cyberdrop_album_images(snapshot: SnapshotAssertion) -> None:
    items = list(extract(CYBERDROP_URLS["images"]))

    assert items
    for item in items:
        assert_valid_item(item)
    assert normalize_items(items) == snapshot


@pytest.mark.vcr
def test_cyberdrop_album_videos(snapshot: SnapshotAssertion) -> None:
    items = list(extract(CYBERDROP_URLS["videos"]))

    assert items
    for item in items:
        assert_valid_item(item)
    assert normalize_items(items) == snapshot


@pytest.mark.vcr
def test_cyberdrop_single_file(snapshot: SnapshotAssertion) -> None:
    items = list(extract(CYBERDROP_URLS["single_file"]))

    assert len(items) == 1
    assert_valid_item(items[0])
    assert normalize_items(items) == snapshot
