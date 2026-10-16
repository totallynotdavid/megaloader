import pytest

from megaloader import extract
from syrupy.assertion import SnapshotAssertion

from tests.plugins.normalize import normalize_items
from tests.test_urls import FAPELLO_URLS


@pytest.mark.vcr
def test_fapello_model(snapshot: SnapshotAssertion) -> None:
    items = list(extract(FAPELLO_URLS["model"]))

    assert items
    assert normalize_items(items) == snapshot
