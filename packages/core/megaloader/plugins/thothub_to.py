import logging
import re
import time

from collections.abc import Generator
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from megaloader.error_policy import raise_extraction_error
from megaloader.exceptions import ExtractionError
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
    """Classify a Thothub.to URL as a video, an album, a model, or unsupported."""
    path = urlparse(url).path
    if path.startswith("/videos/"):
        return Video(url)
    if path.startswith("/albums/"):
        return Album(url)
    if path.startswith("/models/"):
        return Model(url)
    return None


def derive_key(license_code: str) -> str:
    """Derive the deobfuscation key from a video's license_code (site algorithm)."""
    f_str = "".join(
        str(int(c)) if c.isdigit() and int(c) != 0 else "1" for c in license_code[1:]
    )
    j = len(f_str) // 2
    k = int(f_str[: j + 1])
    length = int(f_str[j:])
    f2 = str((abs(length - k) + abs(k - length)) * 2)

    key = ""
    for g in range(j + 1):
        for h in range(1, 5):
            try:
                d = int(license_code[g + h])
            except (IndexError, ValueError):
                d = 0
            n = d + int(f2[g % len(f2)])
            if n >= 10:
                n -= 10
            key += str(n)

    return key


def deobfuscate_hash(value: str, key: str) -> str:
    """Reverse the index-swap obfuscation on the CDN path segment."""
    chars = list(value)
    prefix = chars[:32]
    suffix = chars[32:]

    for k in range(len(prefix) - 1, -1, -1):
        swap_idx = (k + sum(int(d) for d in key[k:])) % len(prefix)
        prefix[k], prefix[swap_idx] = prefix[swap_idx], prefix[k]

    return "".join(prefix + suffix)


def deobfuscate_video_url(obfuscated_url: str, license_code: str) -> str:
    """Reconstruct the CDN URL from the page's obfuscated video_url + license_code."""
    parts = obfuscated_url.replace("function/0/", "").split("/")
    parts[5] = deobfuscate_hash(parts[5], derive_key(license_code))
    return "/".join(parts)


def parse_video_metadata(page: str, url: str) -> tuple[str, str, str]:
    """Return (obfuscated_video_url, license_code, title) from a video page."""
    video_id = re.search(r"video_id:\s*'(\d+)'", page)
    video_url = re.search(r"video_url:\s*'([^']+)'", page)
    license_code = re.search(r"license_code:\s*'(\$.+?)'", page)

    if not (video_id and video_url and license_code):
        raise_extraction_error(
            f"Could not extract video metadata: {url}",
            source="thothubto",
            url=url,
            category="protocol",
        )

    soup = BeautifulSoup(page, "html.parser")
    h1 = soup.find("h1")
    title = h1.text.strip() if h1 else f"video_{video_id.group(1)}"

    return video_url.group(1), license_code.group(1), title


def parse_album(page: str, base_url: str) -> tuple[str, list[tuple[str, str]]]:
    """Return (collection_name, [(url, filename)]) from an album page."""
    soup = BeautifulSoup(page, "html.parser")

    h1 = soup.find("h1")
    collection_name = h1.text.strip() if h1 else "album"

    files: list[tuple[str, str]] = []
    for link in soup.select('div.block-album a.item[href*="/get_image/"]'):
        if href := link.get("href"):
            full_url = urljoin(base_url, str(href))
            files.append((full_url, filename_from_url(full_url)))

    return collection_name, files


def parse_model_video_links(page: str, base_url: str) -> list[str]:
    """Return absolute video URLs from one paginated model listing page."""
    soup = BeautifulSoup(page, "html.parser")
    return [
        urljoin(base_url, str(link["href"]))
        for link in soup.select('div.item > a[href*="/videos/"]')
        if link.get("href")
    ]


class ThothubTO(BasePlugin):
    """Extract content from Thothub.to."""

    def extract(self, fetch: Fetcher) -> Generator[DownloadItem, None, None]:
        target = parse_target(self.url)

        if isinstance(target, Video):
            yield self._fetch_video(fetch, target.url)
        elif isinstance(target, Album):
            yield from self._extract_album(fetch, target.url)
        elif isinstance(target, Model):
            yield from self._extract_model(fetch, target.url)
        else:
            logger.warning("Unrecognized Thothub URL format")

    def _fetch_video(
        self, fetch: Fetcher, url: str, collection_name: str | None = None
    ) -> DownloadItem:
        response = fetch(Request(url))
        obfuscated_url, license_code, title = parse_video_metadata(response.text, url)

        cdn_url = deobfuscate_video_url(obfuscated_url, license_code)
        final_url = f"{cdn_url}?rnd={int(time.time() * 1000)}"

        return DownloadItem(
            download_url=final_url,
            filename=f"{title}.mp4",
            collection_name=collection_name,
            headers={"Referer": url},
        )

    def _extract_album(
        self, fetch: Fetcher, url: str
    ) -> Generator[DownloadItem, None, None]:
        response = fetch(Request(url))
        collection_name, files = parse_album(response.text, url)

        for full_url, filename in files:
            yield DownloadItem(
                download_url=full_url,
                filename=filename,
                collection_name=collection_name,
            )

    def _extract_model(
        self, fetch: Fetcher, url: str
    ) -> Generator[DownloadItem, None, None]:
        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        model_name = parsed.path.split("/")[2]
        page = 1
        seen: set[str] = set()

        while True:
            pagination_url = (
                f"{base_url}/models/{model_name}/"
                f"?mode=async&function=get_block&block_id=list_videos_common_videos_list"
                f"&sort_by=post_date&from={page}"
            )

            try:
                response = fetch(Request(pagination_url))
            except ExtractionError as e:
                if e.http_status == 404:
                    break
                raise

            if not response.text.strip():
                break

            video_urls = parse_model_video_links(response.text, base_url)
            if not video_urls:
                break

            for video_url in video_urls:
                if video_url in seen:
                    continue

                seen.add(video_url)
                yield self._fetch_video(fetch, video_url, model_name)

            page += 1
