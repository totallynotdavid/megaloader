import pytest

from megaloader.plugins.thotslife import Thotslife, parse_post

from tests.helpers import fake_fetcher


POST_URL = "https://thotslife.com/some-post/"


def _post_page(body: str, title: str = "Some Post") -> str:
    return (
        f'<h1 class="entry-title">{title}</h1><div itemprop="articleBody">{body}</div>'
    )


@pytest.mark.unit
def test_parse_post_collects_videos_then_images_without_duplicates() -> None:
    page = _post_page(
        '<video><source src="https://cdn.thotslife.com/a.mp4"></video>'
        '<video><source src="https://cdn.thotslife.com/a.mp4"></video>'
        '<img data-src="https://cdn.thotslife.com/b.jpg">'
        '<img data-src="https://cdn.thotslife.com/b.jpg">'
    )

    collection_name, media = parse_post(page)

    assert collection_name == "Some Post"
    assert media == [
        ("https://cdn.thotslife.com/a.mp4", "a.mp4"),
        ("https://cdn.thotslife.com/b.jpg", "b.jpg"),
    ]


@pytest.mark.unit
def test_parse_post_skips_base64_embedded_images() -> None:
    page = _post_page('<img data-src="data:image/gif;base64,R0lGODlh">')

    assert parse_post(page) == ("Some Post", [])


@pytest.mark.unit
def test_parse_post_falls_back_to_collection_based_names() -> None:
    # A URL whose path carries no leaf name would produce an empty filename, so
    # videos borrow the post title and images fall back to a generic name.
    page = _post_page(
        '<video><source src="https://cdn.thotslife.com/"></video>'
        '<img data-src="https://img.thotslife.com/">'
    )

    _, media = parse_post(page)

    assert [filename for _, filename in media] == ["Some Post.mp4", "image.jpg"]


@pytest.mark.unit
def test_parse_post_without_article_body_returns_no_media() -> None:
    assert parse_post('<h1 class="entry-title">Some Post</h1>') == ("Some Post", [])


@pytest.mark.unit
def test_parse_post_without_title_uses_a_generic_collection_name() -> None:
    collection_name, media = parse_post(
        '<div itemprop="articleBody"><img data-src="https://cdn/a.jpg"></div>'
    )

    assert collection_name == "thotslife_post"
    assert media == [("https://cdn/a.jpg", "a.jpg")]


@pytest.mark.unit
def test_extract_yields_one_item_per_media_entry() -> None:
    routes = {
        POST_URL: _post_page(
            '<video><source src="https://cdn.thotslife.com/a.mp4"></video>'
            '<img data-src="https://cdn.thotslife.com/b.jpg">'
        )
    }

    items = list(Thotslife(POST_URL).extract(fake_fetcher(routes)))

    assert [item.filename for item in items] == ["a.mp4", "b.jpg"]
    assert {item.collection_name for item in items} == {"Some Post"}
