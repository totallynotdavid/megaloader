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
            if item := self._fetch_video(self.url):
                yield item
        elif "/album/" in self.url:
            yield from self._fetch_album(self.url)
        elif "/models/" in self.url:
            yield from self._extract_model()
        else:
            logger.warning("Unsupported ThothubVIP URL format")

    def _extract_model(self) -> Generator[DownloadItem, None, None]:
        """Extract all videos and albums from a model page."""
        response = self.session.get(self.url, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Get model name for collection
        title_div = soup.find("div", class_="title")
        model_name = title_div.text.strip() if title_div else None

        seen = set()

        # Extract video links
        for link in soup.select('a[href*="/video/"]'):
            if (href := link.get("href")) and (
                video_url := urljoin(self.url, str(href))
            ) not in seen:
                seen.add(video_url)
                if item := self._fetch_video(video_url, model_name):
                    yield item

        # Extract album links
        for link in soup.select('a[href*="/album/"]'):
            if (href := link.get("href")) and (
                album_url := urljoin(self.url, str(href))
            ) not in seen:
                seen.add(album_url)
                yield from self._fetch_album(album_url)

    def _fetch_video(
        self, video_url: str, collection_name: str | None = None
    ) -> DownloadItem | None:
        """Fetch video metadata from URL."""
        try:
            response = self.session.get(video_url, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            script = soup.find("script", type="application/ld+json")

            if not script:
                return None

            metadata = json.loads(script.get_text().strip())

            if url := metadata.get("contentUrl"):
                title = metadata.get("name", "video")
                return DownloadItem(
                    download_url=urljoin(video_url, url),
                    filename=f"{title}.mp4",
                    collection_name=collection_name,
                )
        except Exception:
            logger.debug("Failed to fetch video from %s", video_url, exc_info=True)

        return None

    def _fetch_album(self, album_url: str) -> Generator[DownloadItem, None, None]:
        """Fetch album images from URL."""
        try:
            response = self.session.get(album_url, timeout=30)
            response.raise_for_status()
        except Exception:
            logger.debug("Failed to fetch album from %s", album_url, exc_info=True)
            return

        soup = BeautifulSoup(response.text, "html.parser")
        h1 = soup.find("h1", class_="title")
        collection_name = h1.text.strip() if h1 else "album"

        for link in soup.select("div.album-inner a.item.album-img[href]"):
            if href := link.get("href"):
                full_url = urljoin(album_url, str(href))
                filename = Path(urlparse(full_url).path.strip("/")).name

                if filename:
                    yield DownloadItem(
                        download_url=full_url,
                        filename=filename,
                        collection_name=collection_name,
                    )
