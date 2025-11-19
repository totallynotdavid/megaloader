import json
import logging
import re

from collections.abc import Generator

from megaloader.item import DownloadItem
from megaloader.plugin import BasePlugin


logger = logging.getLogger(__name__)


class PixelDrain(BasePlugin):
    """Extract files from Pixeldrain lists and individual files."""

    def extract(self) -> Generator[DownloadItem, None, None]:
        logger.debug("Processing PixelDrain URL: %s", self.url)

        response = self.session.get(self.url, timeout=30)
        response.raise_for_status()

        # Extract embedded viewer data
        match = re.search(
            r"window\.viewer_data\s*=\s*({.*?});", response.text, re.DOTALL
        )
        if not match:
            raise ValueError("Could not find viewer data on page")

        data = json.loads(match.group(1))
        api_response = data.get("api_response", {})

        # List of files
        if data.get("type") == "list" and "files" in api_response:
            for file_data in api_response["files"]:
                yield DownloadItem(
                    download_url=f"https://pixeldrain.com/api/file/{file_data['id']}",
                    filename=file_data["name"],
                    source_id=file_data["id"],
                    size_bytes=file_data.get("size"),
                )

        # Single file
        elif "name" in api_response:
            yield DownloadItem(
                download_url=f"https://pixeldrain.com/api/file/{api_response['id']}",
                filename=api_response["name"],
                source_id=api_response["id"],
                size_bytes=api_response.get("size"),
            )
