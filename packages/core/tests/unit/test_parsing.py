import pytest

from megaloader.plugins.rule34 import parse_api_posts


@pytest.mark.unit
def test_parse_api_posts_returns_post_elements() -> None:
    xml = (
        b'<posts count="2">'
        b'<post id="10" file_url="https://img.rule34.xxx/a.jpg"/>'
        b'<post id="11" file_url="https://img.rule34.xxx/b.png"/>'
        b"</posts>"
    )

    posts = parse_api_posts(xml)

    assert posts is not None
    assert [p.get("id") for p in posts] == ["10", "11"]
    assert [p.get("file_url") for p in posts] == [
        "https://img.rule34.xxx/a.jpg",
        "https://img.rule34.xxx/b.png",
    ]


@pytest.mark.unit
def test_parse_api_posts_returns_none_for_non_xml() -> None:
    # The API answers rate limits and outages with plain text, not XML.
    assert parse_api_posts(b"503 Service Temporarily Unavailable") is None
