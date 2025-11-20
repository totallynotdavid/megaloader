import pytest

from megaloader.plugins.fapello import Fapello

from tests.helpers import assert_valid_item
from tests.test_urls import FAPELLO_URLS


@pytest.mark.live
def test_fapello_model():
    """Test Fapello model page extraction."""
    url = FAPELLO_URLS["model"]

    plugin = Fapello(url)
    items = list(plugin.extract())

    assert len(items) > 0, f"No items extracted from {url}"

    for item in items:
        assert_valid_item(item)
