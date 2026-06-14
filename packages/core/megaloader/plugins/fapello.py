import logging
import re

from collections.abc import Generator
from typing import Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from megaloader.fetcher import Fetcher, Request, SessionConfig
from megaloader.filenames import filename_from_url
from megaloader.item import DownloadItem
from megaloader.plugin import BasePlugin


logger = logging.getLogger(__name__)


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
        return SessionConfig(headers={"Referer": "https://fapello.com/"})

    def extract(self, fetch: Fetcher) -> Generator[DownloadItem, None, None]:
        logger.debug("Extracting Fapello model: %s", self.model_name)

        page = 1
        seen_urls: set[str] = set()

        while True:
            ajax_url = f"https://fapello.com/ajax/model/{self.model_name}/page-{page}/"
            response = fetch(Request(ajax_url))

            if not response.text.strip():
                break

            soup = BeautifulSoup(response.text, "html.parser")
            thumbnails = soup.select('a > div > img[src*="/content/"]')

            if not thumbnails:
                break

            for img in thumbnails:
                thumb_url = urljoin("https://fapello.com/", str(img["src"]))
                full_url = full_resolution_url(thumb_url)

                if full_url not in seen_urls:
                    seen_urls.add(full_url)

                    yield DownloadItem(
                        download_url=full_url,
                        filename=filename_from_url(full_url),
                        collection_name=self.model_name,
                    )

            page += 1
