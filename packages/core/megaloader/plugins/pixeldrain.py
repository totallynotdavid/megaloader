import json
import logging
import re

from collections.abc import Generator

from megaloader.error_policy import raise_extraction_error
from megaloader.item import DownloadItem
from megaloader.plugin import BasePlugin


logger = logging.getLogger(__name__)


class PixelDrain(BasePlugin):
    """Extract files from Pixeldrain lists and individual files."""

    def extract(self) -> Generator[DownloadItem, None, None]:
        logger.debug("Processing PixelDrain URL: %s", self.url)

        response = self._get(self.url)

        # Extract embedded viewer data
        match = re.search(
            r"window\.viewer_data\s*=\s*({.*?});", response.text, re.DOTALL
        )
        if not match:
            raise_extraction_error(
                "Could not find viewer data on page",
                source="pixeldrain",
                url=self.url,
                category="protocol",
            )

        data = json.loads(match.group(1))
        api_response = data.get("api_response", {})

        if data.get("type") == "list" and "files" in api_response:
            for file_data in api_response["files"]:
                yield DownloadItem(
                    download_url=f"https://pixeldrain.com/api/file/{file_data['id']}",
                    filename=file_data["name"],
                    source_id=file_data["id"],
                    size_bytes=file_data.get("size"),
                )

        elif "name" in api_response:
            yield DownloadItem(
                download_url=f"https://pixeldrain.com/api/file/{api_response['id']}",
                filename=api_response["name"],
                source_id=api_response["id"],
                size_bytes=api_response.get("size"),
            )
