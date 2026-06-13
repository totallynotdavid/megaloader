import json
import logging
import re

from collections.abc import Generator
from typing import Any

from megaloader.error_policy import raise_extraction_error
from megaloader.fetcher import Fetcher, Request
from megaloader.item import DownloadItem
from megaloader.plugin import BasePlugin


logger = logging.getLogger(__name__)


def parse_viewer_data(page: str, url: str) -> dict[str, Any]:
    """Extract the embedded window.viewer_data JSON blob from a Pixeldrain page."""
    match = re.search(r"window\.viewer_data\s*=\s*({.*?});", page, re.DOTALL)
    if not match:
        raise_extraction_error(
            "Could not find viewer data on page",
            source="pixeldrain",
            url=url,
            category="protocol",
        )

    data: dict[str, Any] = json.loads(match.group(1))
    return data


def items_from_viewer_data(data: dict[str, Any]) -> list[DownloadItem]:
    """Build download items from viewer_data, handling both list and single-file pages."""
    api_response = data.get("api_response", {})

    if data.get("type") == "list" and "files" in api_response:
        return [
            DownloadItem(
                download_url=f"https://pixeldrain.com/api/file/{file_data['id']}",
                filename=file_data["name"],
                source_id=file_data["id"],
                size_bytes=file_data.get("size"),
            )
            for file_data in api_response["files"]
        ]

    if "name" in api_response:
        return [
            DownloadItem(
                download_url=f"https://pixeldrain.com/api/file/{api_response['id']}",
                filename=api_response["name"],
                source_id=api_response["id"],
                size_bytes=api_response.get("size"),
            )
        ]

    return []


class PixelDrain(BasePlugin):
    """Extract files from Pixeldrain lists and individual files."""

    def extract(self, fetch: Fetcher) -> Generator[DownloadItem, None, None]:
        logger.debug("Processing PixelDrain URL: %s", self.url)

        response = fetch(Request(self.url))
        data = parse_viewer_data(response.text, self.url)
        yield from items_from_viewer_data(data)
