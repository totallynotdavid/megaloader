import pytest

from megaloader import extract
from syrupy.assertion import SnapshotAssertion

from tests.plugins.normalize import normalize_items
from tests.test_urls import GOFILE_URLS


@pytest.mark.vcr
def test_gofile_folder_images(snapshot: SnapshotAssertion) -> None:
    items = list(extract(GOFILE_URLS["images"]))

    assert items
    assert normalize_items(items) == snapshot


@pytest.mark.vcr
def test_gofile_folder_videos(snapshot: SnapshotAssertion) -> None:
    items = list(extract(GOFILE_URLS["videos"]))

    assert items
    assert normalize_items(items) == snapshot
