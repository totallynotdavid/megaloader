import base64
import html
import logging
import math
import re

from collections.abc import Generator
from urllib.parse import quote, urljoin, urlparse

import requests

from megaloader.item import DownloadItem
from megaloader.plugin import BasePlugin


logger = logging.getLogger(__name__)


class Bunkr(BasePlugin):
    """Extract files from Bunkr albums and individual file pages."""

    API_BASE = "https://apidl.bunkr.ru/api/_001_v2"

    def extract(self) -> Generator[DownloadItem, None, None]:
        path = urlparse(self.url).path

        if path.startswith("/a/"):
            logger.debug("Processing album")
            yield from self._extract_album()
        elif path.startswith("/f/"):
            logger.debug("Processing single file")
            yield from self._extract_file(self.url)
        else:
            logger.warning("Unrecognized Bunkr URL format")

    def _extract_album(self) -> Generator[DownloadItem, None, None]:
        """Extract all files from an album page."""
        try:
            response = self.session.get(self.url, allow_redirects=True, timeout=30)
            response.raise_for_status()
        except Exception:
            logger.exception("Failed to fetch album page")
            return

        file_links = re.findall(r'href="(/f/[^"]+)"', response.text)

        if not file_links:
            logger.warning("No files found in album")
            return

        seen_urls = set()
        for link in file_links:
            # Skip template variables
            if "file.slug" in link or "+" in link:
                continue

            file_url = urljoin(response.url, link)
            if file_url in seen_urls:
                continue

            seen_urls.add(file_url)
            yield from self._extract_file(file_url)

    def _extract_file(self, file_url: str) -> Generator[DownloadItem, None, None]:
        """Extract download URL from a file page."""
        try:
            response = self.session.get(file_url, timeout=30)
            response.raise_for_status()
        except requests.RequestException:
            logger.debug("Failed to fetch file page %s", file_url, exc_info=True)
            return

        # Find download button
        download_match = re.search(
            r'<a[^>]+class="[^"]*btn-main[^"]*"[^>]+href="([^"]+)"[^>]*>Download</a>',
            response.text,
        )

        if not download_match:
            logger.debug("No download button found for %s", file_url)
            return

        download_page_url = urljoin(file_url, download_match.group(1))

        # Extract file ID from download page URL
        if match := re.search(r"/file/(\w+)", download_page_url):
            file_id = match.group(1)
        else:
            logger.debug("Could not extract file ID from %s", download_page_url)
            return

        filename = self._extract_filename(response.text) or f"bunkr_file_{file_id}"

        if direct_url := self._fetch_direct_url(file_id, filename):
            yield DownloadItem(
                download_url=direct_url,
                filename=filename,
                source_id=file_id,
            )

    def _extract_filename(self, content: str) -> str | None:
        """Extract original filename from page metadata."""
        # Try og:title meta tag
        if match := re.search(r'<meta property="og:title" content="([^"]+)"', content):
            return html.unescape(match.group(1)).strip()

        # Try JavaScript variable
        if match := re.search(r'var ogname\s*=\s*"([^"]+)"', content):
            return html.unescape(match.group(1)).strip()

        return None

    def _fetch_direct_url(self, file_id: str, filename: str) -> str | None:
        """Get direct CDN URL using Bunkr's API."""
        try:
            response = self.session.post(
                self.API_BASE,
                json={"id": file_id},
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()

            # Decrypt the URL
            timestamp = data["timestamp"]
            encrypted_b64 = data["url"]

            # Generate time-based decryption key
            key_str = f"SECRET_KEY_{math.floor(timestamp / 3600)}"
            key_bytes = key_str.encode("utf-8")

            # XOR decrypt
            encrypted_bytes = base64.b64decode(encrypted_b64)
            decrypted = bytearray(
                encrypted_bytes[i] ^ key_bytes[i % len(key_bytes)]
                for i in range(len(encrypted_bytes))
            )

            base_url = decrypted.decode("utf-8")
            return f"{base_url}?n={quote(filename)}"

        except Exception:
            logger.debug(
                "Failed to fetch direct URL for file ID %s", file_id, exc_info=True
            )
            return None
