import logging

from collections.abc import Generator

from bs4 import BeautifulSoup, Tag

from megaloader.fetcher import Fetcher, Request
from megaloader.filenames import filename_from_url
from megaloader.item import DownloadItem
from megaloader.plugin import BasePlugin


logger = logging.getLogger(__name__)


def parse_post(page: str) -> tuple[str, list[tuple[str, str]]]:
    """Return (collection_name, [(url, filename)]) for media in a Thotslife post."""
    soup = BeautifulSoup(page, "html.parser")

    title_tag = soup.find("h1", class_="entry-title")
    collection_name = title_tag.text.strip() if title_tag else "thotslife_post"

    body = soup.find("div", itemprop="articleBody")
    if not isinstance(body, Tag):
        return collection_name, []

    media: list[tuple[str, str]] = []
    seen: set[str] = set()

    for source in body.select("video > source[src]"):
        if src := source.get("src"):
            src_str = str(src)
            if src_str not in seen:
                seen.add(src_str)
                filename = filename_from_url(src_str, f"{collection_name}.mp4")
                media.append((src_str, filename))

    for img in body.select("img[data-src]"):
        if src := img.get("data-src"):
            src_str = str(src)

            # Skip base64 embedded images
            if not src_str.startswith("data:") and src_str not in seen:
                seen.add(src_str)
                filename = filename_from_url(src_str, "image.jpg")
                media.append((src_str, filename))

    return collection_name, media


class Thotslife(BasePlugin):
    """Extract media from Thotslife posts."""

    def extract(self, fetch: Fetcher) -> Generator[DownloadItem, None, None]:
        response = fetch(Request(self.url))
        collection_name, media = parse_post(response.text)

        for url, filename in media:
            yield DownloadItem(
                download_url=url,
                filename=filename,
                collection_name=collection_name,
            )
