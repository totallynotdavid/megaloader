import logging
import re

from collections.abc import Generator
from typing import Any
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from megaloader.plugin import BasePlugin, Item


logger = logging.getLogger(__name__)


class Cyberdrop(BasePlugin):
    API_BASE_URL = "https://api.cyberdrop.cr/api/file"
    BASE_URL = "https://cyberdrop.cr"
    INVALID_FILENAME_CHARS = r'[<>:"/\\|?*]'

    def _sanitize_name(self, name: str) -> str:
        return re.sub(self.INVALID_FILENAME_CHARS, "_", name).strip()

    def _get_file_info(self, file_id: str) -> dict[str, Any] | None:
        api_url = f"{self.API_BASE_URL}/info/{file_id}"
        try:
            response = self.session.get(api_url, timeout=30)
            response.raise_for_status()
            data: dict[str, Any] = response.json()
            if data.get("name") and data.get("auth_url"):
                return data
        except Exception:
            logger.exception("Failed to get file info for ID %s", file_id)
        return None

    def extract(self) -> Generator[Item, None, None]:
        parsed_url = urlparse(self.url)
        if parsed_url.path.startswith("/a/"):
            yield from self._export_album()
        elif parsed_url.path.startswith("/f/"):
            yield from self._export_single_file()
        else:
            logger.warning("Unrecognized Cyberdrop URL format")

    def _export_album(self) -> Generator[Item, None, None]:
        try:
            response = self.session.get(self.url, timeout=30)
            response.raise_for_status()
        except Exception:
            logger.exception("Failed to fetch album page")
            return

        soup = BeautifulSoup(response.text, "html.parser")
        title_el = soup.find("h1", id="title")
        album_title = (
            self._sanitize_name(title_el.text) if title_el else "cyberdrop_album"
        )

        file_links = soup.select("a.file[href], a#file[href]")
        for link in file_links:
            file_url = urljoin(self.BASE_URL, str(link["href"]))
            if match := re.search(r"/f/(\w+)", file_url):
                file_id = match.group(1)
                if info := self._get_file_info(file_id):
                    yield Item(
                        url=info["auth_url"],
                        filename=self._sanitize_name(info["name"]),
                        album=album_title,
                        id=file_id,
                    )

    def _export_single_file(self) -> Generator[Item, None, None]:
        if match := re.search(r"/f/(\w+)", self.url):
            file_id = match.group(1)
            if info := self._get_file_info(file_id):
                yield Item(
                    url=info["auth_url"],
                    filename=self._sanitize_name(info["name"]),
                    id=file_id,
                )
