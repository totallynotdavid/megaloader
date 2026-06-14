import json
import logging

from collections.abc import Generator
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from megaloader.error_policy import raise_extraction_error
from megaloader.fetcher import Fetcher, Request
from megaloader.filenames import filename_from_url
from megaloader.item import DownloadItem
from megaloader.plugin import BasePlugin


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Video:
    url: str


@dataclass(frozen=True)
class Album:
    url: str


@dataclass(frozen=True)
class Model:
    url: str


Target = Video | Album | Model | None


def parse_target(url: str) -> Target:
    """Classify a Thothub.vip URL as a video, an album, a model, or unsupported."""
    path = urlparse(url).path
    if path.startswith("/video/"):
        return Video(url)
    if path.startswith("/album/"):
        return Album(url)
    if path.startswith("/models/"):
        return Model(url)
    return None


def parse_model_links(
    page: str, base_url: str
) -> tuple[str | None, list[str], list[str]]:
    """Return (model_name, video_urls, album_urls) from a model page, deduped in order."""
    soup = BeautifulSoup(page, "html.parser")

    title_div = soup.find("div", class_="title")
    model_name = title_div.text.strip() if title_div else None

    seen: set[str] = set()

    video_urls: list[str] = []
    for link in soup.select('a[href*="/video/"]'):
        if (href := link.get("href")) and (
            video_url := urljoin(base_url, str(href))
        ) not in seen:
            seen.add(video_url)
            video_urls.append(video_url)

    album_urls: list[str] = []
    for link in soup.select('a[href*="/album/"]'):
        if (href := link.get("href")) and (
            album_url := urljoin(base_url, str(href))
        ) not in seen:
            seen.add(album_url)
            album_urls.append(album_url)

    return model_name, video_urls, album_urls


def parse_video_metadata(page: str, video_url: str) -> tuple[str, str]:
    """Return (content_url, title) from a video page's ld+json metadata."""
    soup = BeautifulSoup(page, "html.parser")
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

    return str(url), str(metadata.get("name", "video"))


def parse_album(page: str, album_url: str) -> tuple[str, list[tuple[str, str]]]:
    """Return (collection_name, [(url, filename)]) from an album page."""
    soup = BeautifulSoup(page, "html.parser")

    h1 = soup.find("h1", class_="title")
    collection_name = h1.text.strip() if h1 else "album"

    files: list[tuple[str, str]] = []
    for link in soup.select("div.album-inner a.item.album-img[href]"):
        if href := link.get("href"):
            full_url = urljoin(album_url, str(href))
            filename = filename_from_url(full_url)
            if filename:
                files.append((full_url, filename))

    return collection_name, files


class ThothubVIP(BasePlugin):
    """Extract content from Thothub.vip."""

    def extract(self, fetch: Fetcher) -> Generator[DownloadItem, None, None]:
        target = parse_target(self.url)

        if isinstance(target, Video):
            yield self._fetch_video(fetch, target.url)
        elif isinstance(target, Album):
            yield from self._extract_album(fetch, target.url)
        elif isinstance(target, Model):
            yield from self._extract_model(fetch)
        else:
            logger.warning("Unsupported ThothubVIP URL format")

    def _extract_model(self, fetch: Fetcher) -> Generator[DownloadItem, None, None]:
        response = fetch(Request(self.url))
        model_name, video_urls, album_urls = parse_model_links(response.text, self.url)

        for video_url in video_urls:
            yield self._fetch_video(fetch, video_url, model_name)

        for album_url in album_urls:
            yield from self._extract_album(fetch, album_url)

    def _fetch_video(
        self, fetch: Fetcher, video_url: str, collection_name: str | None = None
    ) -> DownloadItem:
        response = fetch(Request(video_url))
        content_url, title = parse_video_metadata(response.text, video_url)

        return DownloadItem(
            download_url=urljoin(video_url, content_url),
            filename=f"{title}.mp4",
            collection_name=collection_name,
        )

    def _extract_album(
        self, fetch: Fetcher, album_url: str
    ) -> Generator[DownloadItem, None, None]:
        response = fetch(Request(album_url))
        collection_name, files = parse_album(response.text, album_url)

        for full_url, filename in files:
            yield DownloadItem(
                download_url=full_url,
                filename=filename,
                collection_name=collection_name,
            )
