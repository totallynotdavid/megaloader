import json
import logging

from collections.abc import Generator
from pathlib import Path
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from megaloader.item import DownloadItem
from megaloader.plugin import BasePlugin


logger = logging.getLogger(__name__)


class ThothubVIP(BasePlugin):
    """Extract content from Thothub.vip."""

    def extract(self) -> Generator[DownloadItem, None, None]:
        if "/video/" in self.url:
            yield from self._extract_video()
        elif "/album/" in self.url:
            yield from self._extract_album()
        else:
            logger.warning("Unsupported ThothubVIP URL format")

    def _extract_video(self) -> Generator[DownloadItem, None, None]:
        """Extract video using JSON-LD metadata."""
        response = self.session.get(self.url, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        script = soup.find("script", type="application/ld+json")

        if not script:
            return

        try:
            metadata = json.loads(script.get_text().strip())

            if url := metadata.get("contentUrl"):
                title = metadata.get("name", "video")
                yield DownloadItem(
                    download_url=urljoin(self.url, url),
                    filename=f"{title}.mp4",
                )
        except (json.JSONDecodeError, AttributeError):
            logger.debug("Failed to parse JSON-LD", exc_info=True)

    def _extract_album(self) -> Generator[DownloadItem, None, None]:
        """Extract images from album."""
        response = self.session.get(self.url, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        h1 = soup.find("h1", class_="title")
        collection_name = h1.text.strip() if h1 else "album"

        for link in soup.select("div.album-inner a.item.album-img[href]"):
            if href := link.get("href"):
                full_url = urljoin(self.url, str(href))
                filename = Path(urlparse(full_url).path.strip("/")).name

                if filename:
                    yield DownloadItem(
                        download_url=full_url,
                        filename=filename,
                        collection_name=collection_name,
                    )
