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

    try:
        data: dict[str, Any] = json.loads(match.group(1))
    except ValueError as e:
        raise_extraction_error(
            "Malformed viewer data on page",
            source="pixeldrain",
            url=url,
            category="protocol",
            cause=e,
        )

    return data


def _is_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value)


def item_from_file_data(file_data: Any, url: str) -> DownloadItem:
    """Build one item from a viewer_data file entry, which must carry id and name."""
    if not (
        isinstance(file_data, dict)
        and _is_text(file_data.get("id"))
        and _is_text(file_data.get("name"))
    ):
        raise_extraction_error(
            "Viewer data file entry needs a non-empty string id and name",
            source="pixeldrain",
            url=url,
            category="protocol",
        )

    return DownloadItem(
        download_url=f"https://pixeldrain.com/api/file/{file_data['id']}",
        filename=file_data["name"],
        source_id=file_data["id"],
        size_bytes=file_data.get("size"),
    )


def items_from_viewer_data(data: dict[str, Any], url: str) -> list[DownloadItem]:
    """Build download items from viewer_data, handling both list and single-file pages.

    A list with an empty files array is a genuinely empty album. Viewer data
    that is neither a list nor a named file is a changed page, not an empty one.
    """
    api_response = data.get("api_response", {})
    if not isinstance(api_response, dict):
        api_response = {}

    if data.get("type") == "list" and "files" in api_response:
        files = api_response["files"]
        if not isinstance(files, list):
            raise_extraction_error(
                f"Viewer data files is not a list: {type(files).__name__}",
                source="pixeldrain",
                url=url,
                category="protocol",
            )
        return [item_from_file_data(f, url) for f in files]

    if "name" not in api_response:
        raise_extraction_error(
            f"Viewer data carries no files (type={data.get('type')!r})",
            source="pixeldrain",
            url=url,
            category="protocol",
        )

    return [item_from_file_data(api_response, url)]


class PixelDrain(BasePlugin):
    """Extract files from Pixeldrain lists and individual files."""

    def extract(self, fetch: Fetcher) -> Generator[DownloadItem, None, None]:
        logger.debug("Processing PixelDrain URL: %s", self.url)

        response = fetch(Request(self.url))
        data = parse_viewer_data(response.text, self.url)
        yield from items_from_viewer_data(data, self.url)
