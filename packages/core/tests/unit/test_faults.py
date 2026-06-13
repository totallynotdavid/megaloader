import pytest

from megaloader.error_policy import build_extraction_error
from megaloader.plugins.thothub_to import ThothubTO

from tests.helpers import fake_fetcher


def _pagination_url(page: int) -> str:
    return (
        f"https://thothub.to/models/foo/?mode=async&function=get_block"
        f"&block_id=list_videos_common_videos_list&sort_by=post_date&from={page}"
    )


@pytest.mark.unit
def test_model_traversal_stops_on_404() -> None:
    # The model loop pages until the site 404s past the last page. A recorded
    # cassette can't capture that boundary cleanly, so inject the 404 directly:
    # page 1 yields one video, page 2 raises, and traversal must end with that
    # single item rather than propagating the error.
    video_url = "https://thothub.to/videos/1/clip/"
    page1 = f'<div class="item"><a href="{video_url}">clip</a></div>'
    video_page = (
        "<h1>Clip</h1>"
        "<script>"
        "video_id: '1', "
        "video_url: 'https://cdn.thothub.to/get_file/1/"
        "abcdef0123456789abcdef0123456789/720/v.mp4/function/0/', "
        r"license_code: '$1234567890'"
        "</script>"
    )
    not_found = build_extraction_error(
        "missing", source="thothubto", url=_pagination_url(2), http_status=404
    )
    routes = {
        _pagination_url(1): page1,
        video_url: video_page,
        _pagination_url(2): not_found,
    }

    items = list(
        ThothubTO("https://thothub.to/models/foo/").extract(fake_fetcher(routes))
    )

    assert len(items) == 1
    assert items[0].filename == "Clip.mp4"
