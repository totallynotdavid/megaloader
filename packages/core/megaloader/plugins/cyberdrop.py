import logging
import re

from collections.abc import Generator
from typing import Any
from urllib.parse import urljoin, urlparse

import requests

from bs4 import BeautifulSoup

from megaloader.item import DownloadItem
from megaloader.plugin import BasePlugin


logger = logging.getLogger(__name__)


class Cyberdrop(BasePlugin):
    """Extract files from Cyberdrop albums and individual files."""

    API_BASE = "https://api.cyberdrop.cr/api/file"
    SITE_BASE = "https://cyberdrop.cr"

    def extract(self) -> Generator[DownloadItem, None, None]:
        path = urlparse(self.url).path

        if path.startswith("/a/"):
            logger.debug("Processing album")
            yield from self._extract_album()
        elif path.startswith("/f/"):
            logger.debug("Processing single file")
            yield from self._extract_file()
        else:
            logger.warning("Unrecognized Cyberdrop URL format")

    def _extract_album(self) -> Generator[DownloadItem, None, None]:
        """Extract all files from an album."""
        try:
            response = self.session.get(self.url, timeout=30)
            response.raise_for_status()
        except Exception:
            logger.exception("Failed to fetch album page")
            return

        soup = BeautifulSoup(response.text, "html.parser")

        # Get album title
        title_elem = soup.find("h1", id="title")
        collection_name = title_elem.text.strip() if title_elem else None

        # Find all file links
        file_links = soup.select("a.file[href], a#file[href]")

        for link in file_links:
            file_url = urljoin(self.SITE_BASE, str(link["href"]))

            if match := re.search(r"/f/(\w+)", file_url):
                yield from self._process_file(match.group(1), collection_name)

    def _extract_file(self) -> Generator[DownloadItem, None, None]:
        """Extract a single file."""
        if match := re.search(r"/f/(\w+)", self.url):
            yield from self._process_file(match.group(1))

    def _process_file(
        self, file_id: str, collection_name: str | None = None
    ) -> Generator[DownloadItem, None, None]:
        """Process a single file ID and yield download item."""
        item_data = self._fetch_file_info(file_id)
        if not item_data:
            return

        direct_url = self._fetch_direct_url(item_data["auth_url"])
        if not direct_url:
            return

        yield DownloadItem(
            download_url=direct_url,
            filename=item_data["name"],
            collection_name=collection_name,
            source_id=file_id,
        )

    def _fetch_file_info(self, file_id: str) -> dict[str, Any] | None:
        """Get file metadata from API."""
        api_url = f"{self.API_BASE}/info/{file_id}"

        try:
            response = self.session.get(api_url, timeout=30)
            response.raise_for_status()
            data = response.json()

            if isinstance(data, dict) and data.get("name") and data.get("auth_url"):
                return data
        except (requests.RequestException, ValueError):
            logger.debug("Failed to fetch file info for %s", file_id, exc_info=True)

        return None

    def _fetch_direct_url(self, auth_url: str) -> str | None:
        """Get direct CDN URL from auth endpoint."""
        try:
            response = self.session.get(auth_url, timeout=30)
            response.raise_for_status()
            data = response.json()

            if isinstance(data, dict):
                url = data.get("url")
                if isinstance(url, str):
                    return url

        except (requests.RequestException, ValueError, KeyError):
            logger.debug("Failed to fetch direct URL from %s", auth_url, exc_info=True)

        return None
