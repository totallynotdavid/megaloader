import pytest

from megaloader import extract
from syrupy.assertion import SnapshotAssertion

from tests.plugins.normalize import normalize_items
from tests.test_urls import PIXIV_URLS


@pytest.mark.vcr
def test_pixiv_artwork(snapshot: SnapshotAssertion) -> None:
    items = list(extract(PIXIV_URLS["artwork"]))

    assert items
    assert normalize_items(items) == snapshot
