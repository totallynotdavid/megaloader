import logging
import re

from collections.abc import Generator
from dataclasses import dataclass
from typing import Any
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from megaloader.error_policy import raise_extraction_error
from megaloader.fetcher import Fetcher, Request
from megaloader.item import DownloadItem
from megaloader.plugin import BasePlugin


logger = logging.getLogger(__name__)

_FILE_ID_RE = re.compile(r"/f/(\w+)")


@dataclass(frozen=True)
class Album:
    url: str


@dataclass(frozen=True)
class File:
    file_id: str


Target = Album | File | None


def parse_target(url: str) -> Target:
    """Classify a Cyberdrop URL as an album, a single file, or unsupported."""
    path = urlparse(url).path
    if path.startswith("/a/"):
        return Album(url)
    if path.startswith("/f/") and (match := _FILE_ID_RE.search(url)):
        return File(match.group(1))
    return None


def parse_album_page(page: str, site_base: str) -> tuple[str | None, list[str]]:
    """Return (collection_name, file_ids) from a Cyberdrop album page."""
    soup = BeautifulSoup(page, "html.parser")

    title_elem = soup.find("h1", id="title")
    collection_name = title_elem.text.strip() if title_elem else None

    file_ids: list[str] = []
    for link in soup.select("a.file[href], a#file[href]"):
        file_url = urljoin(site_base, str(link["href"]))
        if match := _FILE_ID_RE.search(file_url):
            file_ids.append(match.group(1))

    return collection_name, file_ids


def file_info_from_payload(payload: Any, file_id: str, api_url: str) -> tuple[str, str]:
    """Validate the file-info API response and return (name, auth_url)."""
    if (
        not isinstance(payload, dict)
        or not payload.get("name")
        or not payload.get("auth_url")
    ):
        raise_extraction_error(
            f"Unexpected API response for file {file_id}",
            source="cyberdrop",
            url=api_url,
            category="protocol",
        )

    return str(payload["name"]), str(payload["auth_url"])


def direct_url_from_payload(payload: Any, auth_url: str) -> str:
    """Validate the auth response and return the direct CDN URL."""
    if not isinstance(payload, dict) or not isinstance(payload.get("url"), str):
        raise_extraction_error(
            f"No direct URL in auth response: {auth_url}",
            source="cyberdrop",
            url=auth_url,
            category="protocol",
        )

    return str(payload["url"])


class Cyberdrop(BasePlugin):
    """Extract files from Cyberdrop albums and individual files."""

    API_BASE = "https://api.cyberdrop.cr/api/file"
    SITE_BASE = "https://cyberdrop.cr"

    def extract(self, fetch: Fetcher) -> Generator[DownloadItem, None, None]:
        target = parse_target(self.url)

        if isinstance(target, Album):
            logger.debug("Processing album")
            yield from self._extract_album(fetch)
        elif isinstance(target, File):
            logger.debug("Processing single file")
            yield from self._process_file(fetch, target.file_id)
        else:
            logger.warning("Unrecognized Cyberdrop URL format")

    def _extract_album(self, fetch: Fetcher) -> Generator[DownloadItem, None, None]:
        response = fetch(Request(self.url))
        collection_name, file_ids = parse_album_page(response.text, self.SITE_BASE)

        for file_id in file_ids:
            yield from self._process_file(fetch, file_id, collection_name)

    def _process_file(
        self, fetch: Fetcher, file_id: str, collection_name: str | None = None
    ) -> Generator[DownloadItem, None, None]:
        name, auth_url = self._fetch_file_info(fetch, file_id)
        direct_url = self._fetch_direct_url(fetch, auth_url)

        yield DownloadItem(
            download_url=direct_url,
            filename=name,
            collection_name=collection_name,
            source_id=file_id,
        )

    def _fetch_file_info(self, fetch: Fetcher, file_id: str) -> tuple[str, str]:
        api_url = f"{self.API_BASE}/info/{file_id}"
        response = fetch(Request(api_url))
        return file_info_from_payload(response.json(), file_id, api_url)

    def _fetch_direct_url(self, fetch: Fetcher, auth_url: str) -> str:
        response = fetch(Request(auth_url))
        return direct_url_from_payload(response.json(), auth_url)
