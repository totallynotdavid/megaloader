import pytest

from megaloader import extract
from syrupy.assertion import SnapshotAssertion

from tests.helpers import assert_valid_item
from tests.plugins.normalize import normalize_items
from tests.test_urls import GOFILE_URLS


@pytest.mark.vcr
def test_gofile_folder_images(snapshot: SnapshotAssertion) -> None:
    items = list(extract(GOFILE_URLS["images"]))

    assert items
    for item in items:
        assert_valid_item(item)
    assert normalize_items(items) == snapshot


@pytest.mark.vcr
def test_gofile_folder_videos(snapshot: SnapshotAssertion) -> None:
    items = list(extract(GOFILE_URLS["videos"]))

    assert items
    for item in items:
        assert_valid_item(item)
    assert normalize_items(items) == snapshot
