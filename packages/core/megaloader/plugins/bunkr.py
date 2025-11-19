import html
import logging
import re

from collections.abc import Generator
from pathlib import Path
from urllib.parse import urljoin, urlparse

from megaloader.item import DownloadItem
from megaloader.plugin import BasePlugin


logger = logging.getLogger(__name__)


class Bunkr(BasePlugin):
    """Extract files from Bunkr albums and individual file pages."""

    def extract(self) -> Generator[DownloadItem, None, None]:
        logger.debug("Processing Bunkr URL: %s", self.url)

        response = self.session.get(self.url, allow_redirects=True, timeout=30)
        response.raise_for_status()

        resolved_url = response.url
        content = response.text

        if "/a/" in resolved_url:
            logger.debug("Detected album URL")
            yield from self._extract_album(content, resolved_url)
        elif "/f/" in resolved_url:
            logger.debug("Detected file URL")
            yield from self._extract_file(resolved_url)
        else:
            logger.warning("Unrecognized Bunkr URL format: %s", resolved_url)

    def _extract_album(
        self, content: str, base_url: str
    ) -> Generator[DownloadItem, None, None]:
        """Extract all files from an album page."""
        file_links = re.findall(r'href="(/f/[^"]+)"', content)

        if not file_links:
            logger.warning("No files found in album")
            return

        seen_urls = set()
        for link in file_links:
            # Skip template variables
            if "file.slug" in link or "+" in link:
                continue

            file_url = urljoin(base_url, link)
            if file_url in seen_urls:
                continue

            seen_urls.add(file_url)
            yield from self._extract_file(file_url)

    def _extract_file(self, file_url: str) -> Generator[DownloadItem, None, None]:
        """Extract download URL from a file page."""
        response = self.session.get(file_url, timeout=30)
        response.raise_for_status()

        # Find download button
        download_match = re.search(
            r'<a[^>]+class="[^"]*btn-main[^"]*"[^>]+href="([^"]+)"[^>]*>Download</a>',
            response.text,
        )

        if not download_match:
            logger.warning("No download button found for %s", file_url)
            return

        download_url = urljoin(file_url, download_match.group(1))
        file_id = Path(urlparse(file_url).path).name
        filename = self._extract_filename(response.text) or f"bunkr_file_{file_id}"

        yield DownloadItem(
            download_url=download_url,
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
