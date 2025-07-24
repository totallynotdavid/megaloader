import json
import logging
import math
import os
import re
from collections.abc import Generator
from typing import ClassVar

import requests

from megaloader.plugin import BasePlugin, Item

logger = logging.getLogger(__name__)


class PixelDrain(BasePlugin):
    # Proxy servers for rate limit bypassing
    # Thanks to https://github.com/sh13y/ - to be used only with user permission.
    PROXIES: ClassVar[list[str]] = [
        "pd1.sriflix.my",
        "pd2.sriflix.my",
        "pd3.sriflix.my",
        "pd4.sriflix.my",
        "pd5.sriflix.my",
        "pd6.sriflix.my",
        "pd7.sriflix.my",
        "pd8.sriflix.my",
        "pd9.sriflix.my",
        "pd10.sriflix.my",
    ]

    def __init__(self, url: str, use_proxy: bool = False, **kwargs):
        super().__init__(url, **kwargs)
        self.use_proxy = use_proxy
        self.proxy_index = 0
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        )

    def export(self) -> Generator[Item, None, None]:
        logger.info(f"Processing PixelDrain URL: {self.url}")

        response = self.session.get(self.url, timeout=30)
        response.raise_for_status()

        # Extract viewer data from JavaScript script on the page
        match = re.search(r"window\.viewer_data\s*=\s*({.*?});", response.text)
        if not match:
            raise ValueError("Could not find viewer data on page")

        data = json.loads(match.group(1))
        api_response = data.get("api_response", {})

        if data.get("type") == "list" and "files" in api_response:
            # File list
            files = api_response["files"]
            total_size = sum(f.get("size", 0) for f in files)
            logger.info(
                f"Found list with {len(files)} files ({self._format_size(total_size)})"
            )

            for file_data in files:
                yield Item(
                    url=f"https://pixeldrain.com/api/file/{file_data['id']}",
                    filename=file_data["name"],
                    file_id=file_data["id"],
                    metadata={"size": file_data.get("size", 0)},
                )
        elif "name" in api_response:
            # Single file
            logger.info(
                f"Found single file: {api_response['name']} ({self._format_size(api_response.get('size', 0))})"
            )
            yield Item(
                url=f"https://pixeldrain.com/api/file/{api_response['id']}",
                filename=api_response["name"],
                file_id=api_response["id"],
                metadata={"size": api_response.get("size", 0)},
            )

    def download_file(self, item: Item, output_dir: str) -> bool:
        """Download file from PixelDrain."""
        download_url = self._get_download_url(item.file_id)

        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, item.filename)

        if os.path.exists(output_path):
            logger.info(f"File already exists: {item.filename}")
            return True

        try:
            with requests.get(
                download_url, stream=True, timeout=60, headers=self.session.headers
            ) as response:
                response.raise_for_status()
                with open(output_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)

            logger.info(f"Downloaded: {item.filename}")
            return True

        except Exception as e:
            logger.error(f"Download failed for {item.filename}: {e}")
            if os.path.exists(output_path):
                os.remove(output_path)
            return False

    def _get_download_url(self, file_id: str) -> str:
        """Get download URL, using proxy if enabled."""
        if self.use_proxy:
            proxy = self.PROXIES[self.proxy_index]
            self.proxy_index = (self.proxy_index + 1) % len(self.PROXIES)
            return f"https://{proxy}/api/file/{file_id}?download"
        else:
            return f"https://pixeldrain.com/api/file/{file_id}"

    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human readable format."""
        if size_bytes <= 0:
            return "0B"
        size_names = ("B", "KB", "MB", "GB", "TB")
        i = math.floor(math.log(size_bytes, 1024))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return f"{s} {size_names[i]}"
