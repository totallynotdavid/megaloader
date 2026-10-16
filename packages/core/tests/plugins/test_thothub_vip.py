import pytest

from megaloader import extract
from syrupy.assertion import SnapshotAssertion

from tests.plugins.normalize import normalize_items
from tests.test_urls import THOTHUB_VIP_URLS


@pytest.mark.vcr
def test_thothub_vip_album(snapshot: SnapshotAssertion) -> None:
    items = list(extract(THOTHUB_VIP_URLS["album"]))

    assert items
    assert normalize_items(items) == snapshot


@pytest.mark.vcr
def test_thothub_vip_single_video(snapshot: SnapshotAssertion) -> None:
    items = list(extract(THOTHUB_VIP_URLS["single_video"]))

    assert len(items) == 1
    assert normalize_items(items) == snapshot
