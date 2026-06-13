import base64
import html
import logging
import math
import re

from collections.abc import Generator
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote, urljoin, urlparse

from megaloader.error_policy import raise_extraction_error
from megaloader.fetcher import Fetcher, Request
from megaloader.item import DownloadItem
from megaloader.plugin import BasePlugin


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Album:
    url: str


@dataclass(frozen=True)
class File:
    url: str


Target = Album | File | None


def parse_target(url: str) -> Target:
    """Classify a Bunkr URL as an album, a single file, or unsupported."""
    path = urlparse(url).path
    if path.startswith("/a/"):
        return Album(url)
    if path.startswith("/f/"):
        return File(url)
    return None


def parse_album_links(page: str, base_url: str) -> list[str]:
    """Return absolute, de-duplicated file URLs from an album page, in page order.

    Skips templating placeholders (file.slug, "+") left in the server-rendered
    markup.
    """
    links: list[str] = []
    seen: set[str] = set()
    for href in re.findall(r'href="(/f/[^"]+)"', page):
        if "file.slug" in href or "+" in href:
            continue
        file_url = urljoin(base_url, href)
        if file_url not in seen:
            seen.add(file_url)
            links.append(file_url)
    return links


def parse_download_page_url(page: str, file_url: str) -> str:
    """Find the download-button target on a Bunkr file page."""
    match = re.search(
        r'<a[^>]+class="[^"]*btn-main[^"]*"[^>]+href="([^"]+)"[^>]*>Download</a>',
        page,
    )
    if not match:
        raise_extraction_error(
            f"No download button found: {file_url}",
            source="bunkr",
            url=file_url,
            category="protocol",
        )
    return urljoin(file_url, str(match.group(1)))


def parse_file_id(download_page_url: str, source_url: str) -> str:
    """Pull the opaque file id out of a Bunkr download-page URL."""
    match = re.search(r"/file/(\w+)", download_page_url)
    if not match:
        raise_extraction_error(
            f"Could not extract file ID from: {download_page_url}",
            source="bunkr",
            url=source_url,
            category="protocol",
        )
    return str(match.group(1))


def parse_filename(page: str) -> str | None:
    """Read the display filename from a file page's metadata, if present."""
    if match := re.search(r'<meta property="og:title" content="([^"]+)"', page):
        return html.unescape(match.group(1)).strip()
    if match := re.search(r'var ogname\s*=\s*"([^"]+)"', page):
        return html.unescape(match.group(1)).strip()
    return None


def decrypt_direct_url(payload: dict[str, Any], filename: str) -> str:
    """Decrypt the CDN URL from Bunkr's API payload.

    The API returns a base64 blob XORed with a key that rotates hourly, derived
    from the payload timestamp. Decryption is symmetric, so a recorded payload
    replays deterministically.
    """
    timestamp = payload["timestamp"]
    encrypted = base64.b64decode(payload["url"])

    key = f"SECRET_KEY_{math.floor(timestamp / 3600)}".encode()
    decrypted = bytes(byte ^ key[i % len(key)] for i, byte in enumerate(encrypted))

    return f"{decrypted.decode('utf-8')}?n={quote(filename)}"


class Bunkr(BasePlugin):
    """Extract files from Bunkr albums and individual file pages."""

    API_BASE = "https://apidl.bunkr.ru/api/_001_v2"

    def extract(self, fetch: Fetcher) -> Generator[DownloadItem, None, None]:
        target = parse_target(self.url)

        if isinstance(target, Album):
            logger.debug("Processing album")
            yield from self._extract_album(fetch)
        elif isinstance(target, File):
            logger.debug("Processing single file")
            yield from self._extract_file(fetch, target.url)
        else:
            logger.warning("Unrecognized Bunkr URL format")

    def _extract_album(self, fetch: Fetcher) -> Generator[DownloadItem, None, None]:
        response = fetch(Request(self.url, allow_redirects=True))

        links = parse_album_links(response.text, response.url)
        if not links:
            logger.warning("No files found in album")
            return

        for file_url in links:
            yield from self._extract_file(fetch, file_url)

    def _extract_file(
        self, fetch: Fetcher, file_url: str
    ) -> Generator[DownloadItem, None, None]:
        response = fetch(Request(file_url))

        download_page_url = parse_download_page_url(response.text, file_url)
        file_id = parse_file_id(download_page_url, file_url)
        filename = parse_filename(response.text) or f"bunkr_file_{file_id}"
        direct_url = self._fetch_direct_url(fetch, file_id, filename)

        yield DownloadItem(
            download_url=direct_url,
            filename=filename,
            source_id=file_id,
            headers={"Referer": "https://get.bunkrr.su/"},
        )

    def _fetch_direct_url(self, fetch: Fetcher, file_id: str, filename: str) -> str:
        """Resolve the direct CDN URL via Bunkr's API."""
        response = fetch(Request(self.API_BASE, method="POST", json={"id": file_id}))
        return decrypt_direct_url(response.json(), filename)
