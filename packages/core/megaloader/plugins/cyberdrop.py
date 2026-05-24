import logging
import re

from collections.abc import Generator
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from megaloader.error_policy import raise_extraction_error
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
        response = self._get(self.url)
        soup = BeautifulSoup(response.text, "html.parser")

        title_elem = soup.find("h1", id="title")
        collection_name = title_elem.text.strip() if title_elem else None

        for link in soup.select("a.file[href], a#file[href]"):
            file_url = urljoin(self.SITE_BASE, str(link["href"]))

            if match := re.search(r"/f/(\w+)", file_url):
                yield from self._process_file(match.group(1), collection_name)

    def _extract_file(self) -> Generator[DownloadItem, None, None]:
        if match := re.search(r"/f/(\w+)", self.url):
            yield from self._process_file(match.group(1))

    def _process_file(
        self, file_id: str, collection_name: str | None = None
    ) -> Generator[DownloadItem, None, None]:
        item_data = self._fetch_file_info(file_id)
        direct_url = self._fetch_direct_url(item_data["auth_url"])

        yield DownloadItem(
            download_url=direct_url,
            filename=item_data["name"],
            collection_name=collection_name,
            source_id=file_id,
        )

    def _fetch_file_info(self, file_id: str) -> dict[str, str]:
        api_url = f"{self.API_BASE}/info/{file_id}"
        response = self._get(api_url)
        data = response.json()

        if not isinstance(data, dict) or not data.get("name") or not data.get("auth_url"):
            raise_extraction_error(
                f"Unexpected API response for file {file_id}",
                source="cyberdrop",
                url=api_url,
                category="protocol",
            )

        return {"name": str(data["name"]), "auth_url": str(data["auth_url"])}

    def _fetch_direct_url(self, auth_url: str) -> str:
        response = self._get(auth_url)
        data = response.json()

        if not isinstance(data, dict) or not isinstance(data.get("url"), str):
            raise_extraction_error(
                f"No direct URL in auth response: {auth_url}",
                source="cyberdrop",
                url=auth_url,
                category="protocol",
            )

        return str(data["url"])
