import json
import logging
import os
import re

from collections.abc import Generator
from typing import Any
from urllib.parse import urljoin

import requests

from bs4 import BeautifulSoup

from megaloader.plugin import BasePlugin, Item


logger = logging.getLogger(__name__)


class ThothubVIP(BasePlugin):
    """
    Plugin for downloading videos from thothub.vip.
    It works by parsing the JSON-LD metadata found on video pages.
    """

    _FILENAME_SANITIZE_RE = re.compile(r'[<>:"/\|?*]')

    def __init__(self, url: str, **kwargs: Any) -> None:
        super().__init__(url, **kwargs)
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "https://thothub.vip/",
            }
        )

    def _sanitize_filename(self, filename: str) -> str:
        """Removes illegal characters from a filename."""
        return self._FILENAME_SANITIZE_RE.sub("_", filename).strip()

    def export(self) -> Generator[Item, None, None]:
        """
        Fetches the video page, extracts the JSON-LD metadata, and yields a
        downloadable Item.
        """
        logger.info(f"Processing thothub.vip URL: {self.url}")

        if "/video/" not in self.url:
            logger.warning(
                f"Unsupported URL format: {self.url}. Only /video/ URLs are supported."
            )
            return

        try:
            response = self.session.get(self.url, timeout=30)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Failed to fetch page {self.url}: {e}")
            return

        soup = BeautifulSoup(response.text, "html.parser")
        json_ld_script = soup.find("script", type="application/ld+json")

        if not json_ld_script:
            logger.error("Could not find JSON-LD metadata script on the page.")
            return

        try:
            # Use .string to get the content of the script tag
            metadata = json.loads(json_ld_script.string)
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(f"Failed to parse JSON-LD metadata: {e}")
            return

        if not isinstance(metadata, dict):
            logger.error("Parsed JSON-LD is not a dictionary.")
            return

        content_url = metadata.get("contentUrl")
        video_name = metadata.get("name", "thothub_vip_video")

        if not content_url:
            logger.error("Could not find 'contentUrl' in JSON-LD metadata.")
            return

        # Ensure the URL is absolute
        full_content_url = urljoin(self.url, content_url)

        sanitized_name = self._sanitize_filename(video_name)
        # Assume all videos are mp4 as seen in the example
        filename = f"{sanitized_name}.mp4"

        logger.info(f"Found video: {video_name}")
        yield Item(url=full_content_url, filename=filename)

    def download_file(self, item: Item, output_dir: str) -> bool:
        """
        Downloads a single video file, handling potential redirects from the
        `get_file` URL.
        """
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, item.filename)

        if os.path.exists(output_path):
            logger.info(f"File already exists: {item.filename}")
            return True

        try:
            logger.debug(f"Downloading: {item.url}")
            # The 'get_file' URL likely redirects, so allow_redirects=True is important
            with self.session.get(
                item.url, stream=True, timeout=3600, allow_redirects=True
            ) as response:
                response.raise_for_status()
                with open(output_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
            logger.info(f"Downloaded: {item.filename}")
            return True
        except requests.RequestException as e:
            logger.error(f"Download failed for {item.filename}: {e}")
            if os.path.exists(output_path):
                os.remove(output_path)
            return False
