import logging

from collections.abc import Generator, Iterator

from bs4 import Tag

from megaloader.fetcher import Fetcher, Request
from megaloader.filenames import filename_from_url
from megaloader.item import DownloadItem, items_from_pairs
from megaloader.parsing import element_text, parse_html
from megaloader.plugin import BasePlugin


logger = logging.getLogger(__name__)


def _media_sources(container: Tag, selector: str, attr: str = "src") -> Iterator[str]:
    """Yield asset URLs for matching elements, skipping base64 embedded data."""
    for element in container.select(f"{selector}[{attr}]"):
        if (src := element.get(attr)) and not str(src).startswith("data:"):
            yield str(src)


def parse_post(page: str) -> tuple[str, list[tuple[str, str]]]:
    """Return (collection_name, [(url, filename)]) for media in a Thotslife post."""
    soup = parse_html(page)
    collection_name = element_text(
        soup.find("h1", class_="entry-title"), "thotslife_post"
    )

    body = soup.find("div", itemprop="articleBody")
    if not isinstance(body, Tag):
        return collection_name, []

    # First occurrence of a URL wins, so a video source keeps its .mp4 fallback.
    fallbacks: dict[str, str] = {}
    for src in _media_sources(body, "video > source"):
        fallbacks.setdefault(src, f"{collection_name}.mp4")
    for src in _media_sources(body, "img", attr="data-src"):
        fallbacks.setdefault(src, "image.jpg")

    media = [
        (src, filename_from_url(src, fallback)) for src, fallback in fallbacks.items()
    ]

    return collection_name, media


class Thotslife(BasePlugin):
    """Extract media from Thotslife posts."""

    def extract(self, fetch: Fetcher) -> Generator[DownloadItem, None, None]:
        response = fetch(Request(self.url))
        collection_name, media = parse_post(response.text)

        yield from items_from_pairs(media, collection_name)
