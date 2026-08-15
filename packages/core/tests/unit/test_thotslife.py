import pytest

from megaloader.item import DownloadItem
from megaloader.plugins.thotslife import Thotslife

from tests.helpers import assert_valid_item, fake_fetcher


POST_URL = "https://thotslife.com/some-post/"


def _post_page(body: str, title: str = "Some Post") -> str:
    return (
        f'<h1 class="entry-title">{title}</h1><div itemprop="articleBody">{body}</div>'
    )


def _extract(page: str) -> list[DownloadItem]:
    return list(Thotslife(POST_URL).extract(fake_fetcher({POST_URL: page})))


@pytest.mark.unit
def test_a_post_yields_its_videos_then_its_images_once_each() -> None:
    # Posts commonly repeat the same media in a gallery and a lightbox, so the
    # same file must not be downloaded twice.
    items = _extract(
        _post_page(
            '<video><source src="https://cdn.thotslife.com/a.mp4"></video>'
            '<video><source src="https://cdn.thotslife.com/a.mp4"></video>'
            '<img data-src="https://cdn.thotslife.com/b.jpg">'
            '<img data-src="https://cdn.thotslife.com/b.jpg">'
        )
    )

    for item in items:
        assert_valid_item(item)
    assert [item.download_url for item in items] == [
        "https://cdn.thotslife.com/a.mp4",
        "https://cdn.thotslife.com/b.jpg",
    ]
    assert {item.collection_name for item in items} == {"Some Post"}


@pytest.mark.unit
def test_inline_base64_images_are_not_offered_as_downloads() -> None:
    assert _extract(_post_page('<img data-src="data:image/gif;base64,R0lGODlh">')) == []


@pytest.mark.unit
def test_media_whose_url_carries_no_leaf_name_still_gets_a_usable_filename() -> None:
    items = _extract(
        _post_page(
            '<video><source src="https://cdn.thotslife.com/"></video>'
            '<img data-src="https://img.thotslife.com/">'
        )
    )

    for item in items:
        assert_valid_item(item)
    assert [item.filename for item in items] == ["Some Post.mp4", "image.jpg"]


@pytest.mark.unit
def test_a_post_without_an_article_body_yields_nothing() -> None:
    assert _extract('<h1 class="entry-title">Some Post</h1>') == []


@pytest.mark.unit
def test_an_untitled_post_still_groups_its_media_under_a_collection() -> None:
    items = _extract(
        '<div itemprop="articleBody"><img data-src="https://cdn/a.jpg"></div>'
    )

    assert [item.collection_name for item in items] == ["thotslife_post"]
