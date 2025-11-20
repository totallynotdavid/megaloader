import pytest

from megaloader.plugins.gofile import Gofile

from tests.helpers import assert_valid_item
from tests.test_urls import GOFILE_URLS


@pytest.mark.live
def test_gofile_folder_images():
    """Test Gofile folder extraction with images."""
    url = GOFILE_URLS["images"]

    plugin = Gofile(url)
    items = list(plugin.extract())

    assert len(items) > 0, f"No items extracted from {url}"

    for item in items:
        assert_valid_item(item)


@pytest.mark.live
def test_gofile_folder_videos():
    """Test Gofile folder extraction with videos."""
    url = GOFILE_URLS["videos"]

    plugin = Gofile(url)
    items = list(plugin.extract())

    assert len(items) > 0, f"No items extracted from {url}"

    for item in items:
        assert_valid_item(item)
