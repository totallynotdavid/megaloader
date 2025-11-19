import logging
import re

from collections.abc import Generator
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urljoin, urlparse

import requests

from bs4 import BeautifulSoup

from megaloader.item import DownloadItem
from megaloader.plugin import BasePlugin


logger = logging.getLogger(__name__)


class Fapello(BasePlugin):
    """Extract content from Fapello model pages."""

    def __init__(self, url: str, **options: Any) -> None:
        super().__init__(url, **options)
        self.model_name = self._parse_model_name(url)

    def _parse_model_name(self, url: str) -> str:
        """Extract model name from URL."""
        match = re.search(r"fapello\.com/([a-zA-Z0-9_\-~\.]+)", url)
        if not match or not match.group(1):
            raise ValueError("Invalid Fapello URL")
        return match.group(1).split("/")[0]

    def _configure_session(self, session: requests.Session) -> None:
        session.headers["Referer"] = "https://fapello.com/"

    def extract(self) -> Generator[DownloadItem, None, None]:
        logger.debug("Extracting Fapello model: %s", self.model_name)

        page = 1
        seen_urls = set()

        while True:
            ajax_url = f"https://fapello.com/ajax/model/{self.model_name}/page-{page}/"

            try:
                response = self.session.get(ajax_url, timeout=30)
                response.raise_for_status()

                if not response.text.strip():
                    break
            except Exception:
                logger.debug("Failed to fetch page %d", page, exc_info=True)
                break

            soup = BeautifulSoup(response.text, "html.parser")
            thumbnails = soup.select('a > div > img[src*="/content/"]')

            if not thumbnails:
                break

            for img in thumbnails:
                thumb_url = urljoin("https://fapello.com/", str(img["src"]))

                # Convert thumbnail to full resolution
                full_url = re.sub(
                    r"_\d+px(\.(?:jpg|jpeg|png|mp4))$",
                    r"\1",
                    thumb_url,
                    flags=re.IGNORECASE,
                )

                if full_url not in seen_urls:
                    seen_urls.add(full_url)
                    filename = Path(unquote(urlparse(full_url).path)).name

                    yield DownloadItem(
                        download_url=full_url,
                        filename=filename,
                        collection_name=self.model_name,
                    )

            page += 1
