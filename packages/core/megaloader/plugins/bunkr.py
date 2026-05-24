import base64
import html
import logging
import math
import re

from collections.abc import Generator
from urllib.parse import quote, urljoin, urlparse

from megaloader.error_policy import raise_extraction_error
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
        response = self._get(self.url, allow_redirects=True)

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
        response = self._get(file_url)

        download_match = re.search(
            r'<a[^>]+class="[^"]*btn-main[^"]*"[^>]+href="([^"]+)"[^>]*>Download</a>',
            response.text,
        )

        if not download_match:
            raise_extraction_error(
                f"No download button found: {file_url}",
                source="bunkr",
                url=file_url,
                category="protocol",
            )

        download_page_url = urljoin(file_url, download_match.group(1))

        # Extract file ID from download page URL
        match = re.search(r"/file/(\w+)", download_page_url)
        if not match:
            raise_extraction_error(
                f"Could not extract file ID from: {download_page_url}",
                source="bunkr",
                url=file_url,
                category="protocol",
            )

        file_id = match.group(1)
        filename = self._extract_filename(response.text) or f"bunkr_file_{file_id}"
        direct_url = self._fetch_direct_url(file_id, filename)

        yield DownloadItem(
            download_url=direct_url,
            filename=filename,
            source_id=file_id,
            headers={"Referer": "https://get.bunkrr.su/"},
        )

    def _extract_filename(self, content: str) -> str | None:
        if match := re.search(r'<meta property="og:title" content="([^"]+)"', content):
            return html.unescape(match.group(1)).strip()

        if match := re.search(r'var ogname\s*=\s*"([^"]+)"', content):
            return html.unescape(match.group(1)).strip()

        return None

    def _fetch_direct_url(self, file_id: str, filename: str) -> str:
        """Get direct CDN URL via Bunkr's API (uses XOR decryption with a time-based key)."""
        response = self._post(self.API_BASE, json={"id": file_id})
        data = response.json()

        timestamp = data["timestamp"]
        encrypted_b64 = data["url"]

        # Time-bucketed key changes hourly; decryption is simple XOR
        key_str = f"SECRET_KEY_{math.floor(timestamp / 3600)}"
        key_bytes = key_str.encode("utf-8")

        encrypted_bytes = base64.b64decode(encrypted_b64)
        decrypted = bytearray(
            encrypted_bytes[i] ^ key_bytes[i % len(key_bytes)]
            for i in range(len(encrypted_bytes))
        )

        base_url = decrypted.decode("utf-8")
        return f"{base_url}?n={quote(filename)}"
