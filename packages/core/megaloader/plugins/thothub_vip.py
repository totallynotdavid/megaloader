import json
import logging

from collections.abc import Generator
from pathlib import Path
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from megaloader.error_policy import raise_extraction_error
from megaloader.item import DownloadItem
from megaloader.plugin import BasePlugin


logger = logging.getLogger(__name__)


class ThothubVIP(BasePlugin):
    """Extract content from Thothub.vip."""

    def extract(self) -> Generator[DownloadItem, None, None]:
        path = urlparse(self.url).path

        if path.startswith("/video/"):
            yield self._fetch_video(self.url)
        elif path.startswith("/album/"):
            yield from self._fetch_album(self.url)
        elif path.startswith("/models/"):
            yield from self._extract_model()
        else:
            logger.warning("Unsupported ThothubVIP URL format")

    def _extract_model(self) -> Generator[DownloadItem, None, None]:
        response = self._get(self.url)
        soup = BeautifulSoup(response.text, "html.parser")

        title_div = soup.find("div", class_="title")
        model_name = title_div.text.strip() if title_div else None

        seen: set[str] = set()

        for link in soup.select('a[href*="/video/"]'):
            if (href := link.get("href")) and (
                video_url := urljoin(self.url, str(href))
            ) not in seen:
                seen.add(video_url)
                yield self._fetch_video(video_url, model_name)

        for link in soup.select('a[href*="/album/"]'):
            if (href := link.get("href")) and (
                album_url := urljoin(self.url, str(href))
            ) not in seen:
                seen.add(album_url)
                yield from self._fetch_album(album_url)

    def _fetch_video(
        self, video_url: str, collection_name: str | None = None
    ) -> DownloadItem:
        response = self._get(video_url)
        soup = BeautifulSoup(response.text, "html.parser")
        script = soup.find("script", type="application/ld+json")

        if not script:
            raise_extraction_error(
                f"No video metadata found: {video_url}",
                source="thothubvip",
                url=video_url,
                category="protocol",
            )

        metadata = json.loads(script.get_text().strip())
        url = metadata.get("contentUrl")

        if not url:
            raise_extraction_error(
                f"No contentUrl in video metadata: {video_url}",
                source="thothubvip",
                url=video_url,
                category="protocol",
            )

        title = metadata.get("name", "video")
        return DownloadItem(
            download_url=urljoin(video_url, str(url)),
            filename=f"{title}.mp4",
            collection_name=collection_name,
        )

    def _fetch_album(self, album_url: str) -> Generator[DownloadItem, None, None]:
        response = self._get(album_url)
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
