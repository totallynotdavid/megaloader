import json
import logging

from collections.abc import Generator
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

from megaloader.error_policy import raise_protocol_error
from megaloader.fetcher import Fetcher, Request
from megaloader.filenames import filename_from_url
from megaloader.item import DownloadItem, items_from_pairs
from megaloader.parsing import absolute_links, element_text, parse_html
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
    soup = parse_html(page)
    model_name = element_text(soup.find("div", class_="title"))

    video_urls = absolute_links(soup, 'a[href*="/video/"]', base_url)
    album_urls = absolute_links(soup, 'a[href*="/album/"]', base_url)

    return model_name, video_urls, album_urls


def parse_video_metadata(page: str, video_url: str) -> tuple[str, str]:
    """Return (content_url, title) from a video page's ld+json metadata."""
    soup = parse_html(page)
    script = soup.find("script", type="application/ld+json")

    if not script:
        raise_protocol_error(
            f"No video metadata found: {video_url}",
            source="thothubvip",
            url=video_url,
        )

    metadata = json.loads(script.get_text().strip())
    url = metadata.get("contentUrl")

    if not url:
        raise_protocol_error(
            f"No contentUrl in video metadata: {video_url}",
            source="thothubvip",
            url=video_url,
        )

    return str(url), str(metadata.get("name", "video"))


def parse_album(page: str, album_url: str) -> tuple[str, list[tuple[str, str]]]:
    """Return (collection_name, [(url, filename)]) from an album page."""
    soup = parse_html(page)
    collection_name = element_text(soup.find("h1", class_="title"), "album")

    files = [
        (full_url, filename)
        for full_url in absolute_links(
            soup, "div.album-inner a.item.album-img[href]", album_url
        )
        if (filename := filename_from_url(full_url))
    ]

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

        yield from items_from_pairs(files, collection_name)
