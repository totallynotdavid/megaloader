import logging
import re

from collections.abc import Generator, Iterator
from typing import Any
from urllib.parse import urljoin

from megaloader.fetcher import Fetcher, Request, SessionConfig
from megaloader.filenames import filename_from_url
from megaloader.item import DownloadItem
from megaloader.pagination import crawl_pages
from megaloader.parsing import parse_html, unique
from megaloader.plugin import BasePlugin


logger = logging.getLogger(__name__)

SITE_BASE = "https://fapello.com"


def parse_model_name(url: str) -> str:
    match = re.search(r"fapello\.com/([a-zA-Z0-9_\-~\.]+)", url)
    if not match or not match.group(1):
        msg = "Invalid Fapello URL"
        raise ValueError(msg)
    return match.group(1).split("/")[0]


def full_resolution_url(thumbnail_url: str) -> str:
    """Strip the _<n>px size suffix from a thumbnail URL to get the original asset."""
    return re.sub(
        r"_\d+px(\.(?:jpg|jpeg|png|mp4))$",
        r"\1",
        thumbnail_url,
        flags=re.IGNORECASE,
    )


class Fapello(BasePlugin):
    """Extract content from Fapello model pages."""

    def __init__(self, url: str, **options: Any) -> None:
        super().__init__(url, **options)
        self.model_name = parse_model_name(self.url)

    def session_config(self) -> SessionConfig:
        return SessionConfig(headers={"Referer": f"{SITE_BASE}/"})

    def extract(self, fetch: Fetcher) -> Generator[DownloadItem, None, None]:
        logger.debug("Extracting Fapello model: %s", self.model_name)

        for full_url in unique(self._media_urls(fetch)):
            yield DownloadItem(
                download_url=full_url,
                filename=filename_from_url(full_url),
                collection_name=self.model_name,
            )

    def _media_urls(self, fetch: Fetcher) -> Iterator[str]:
        """Walk the model's ajax pages, yielding full-resolution asset URLs."""
        for response in crawl_pages(fetch, self._page_request):
            soup = parse_html(response.text)
            thumbnails = soup.select('a > div > img[src*="/content/"]')
            if not thumbnails:
                return

            for img in thumbnails:
                yield full_resolution_url(urljoin(SITE_BASE, str(img["src"])))

    def _page_request(self, page: int) -> Request:
        return Request(f"{SITE_BASE}/ajax/model/{self.model_name}/page-{page}/")
