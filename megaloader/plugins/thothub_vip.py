import json
import logging
import os
import re

from collections.abc import Generator
from typing import Any
from urllib.parse import urljoin, urlparse

import requests

from bs4 import BeautifulSoup

from megaloader.plugin import BasePlugin, Item


logger = logging.getLogger(__name__)


class ThothubVIP(BasePlugin):
    """
    Plugin for downloading content from thothub.vip.
    - For videos, it parses JSON-LD metadata.
    - For albums, it scrapes image URLs directly.
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
        Routes the URL to the appropriate handler based on its format
        (e.g., /video/ or /album/).
        """
        logger.info(f"Processing thothub.vip URL: {self.url}")

        if "/video/" in self.url:
            yield from self._export_video()
        elif "/album/" in self.url:
            yield from self._export_album()
        else:
            logger.warning(
                f"Unsupported URL format: {self.url}. Only /video/ and /album/ URLs are supported."
            )
            return

    def _export_video(self) -> Generator[Item, None, None]:
        try:
            response = self.session.get(self.url, timeout=30)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Failed to fetch video page {self.url}: {e}")
            return

        soup = BeautifulSoup(response.text, "html.parser")
        json_ld_script = soup.find("script", type="application/ld+json")

        if not json_ld_script:
            logger.error("Could not find JSON-LD metadata script on the video page.")
            return

        try:
            metadata = json.loads(json_ld_script.get_text().strip())
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

        full_content_url = urljoin(self.url, content_url)
        sanitized_name = self._sanitize_filename(video_name)
        filename = f"{sanitized_name}.mp4"

        logger.info(f"Found video: {video_name}")
        yield Item(url=full_content_url, filename=filename)

    def _export_album(self) -> Generator[Item, None, None]:
        try:
            response = self.session.get(self.url, timeout=30)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Failed to fetch album page {self.url}: {e}")
            return

        soup = BeautifulSoup(response.text, "html.parser")

        title_tag = soup.find("h1", class_="title")
        album_title = title_tag.text.strip() if title_tag else "thothub_vip_album"
        sanitized_album_title = self._sanitize_filename(album_title)

        image_links = soup.select("div.album-inner a.item.album-img[href]")
        if not image_links:
            logger.warning(f"No image links found in album: {album_title}")
            return

        logger.info(f"Found {len(image_links)} images in album '{album_title}'.")
        for link in image_links:
            href = link.get("href")
            if not href:
                continue

            full_image_url = urljoin(self.url, str(href))
            # Extract filename from the URL path, e.g., .../123456.jpg/ -> 123456.jpg
            clean_path = urlparse(full_image_url).path.strip("/")
            filename = os.path.basename(clean_path)

            if not filename:
                logger.warning(
                    f"Could not determine filename for URL: {full_image_url}"
                )
                continue

            yield Item(
                url=full_image_url,
                filename=filename,
                album_title=sanitized_album_title,
            )

    def download_file(self, item: Item, output_dir: str) -> bool:
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, item.filename)

        if os.path.exists(output_path):
            logger.info(f"File already exists: {item.filename}")
            return True

        try:
            logger.debug(f"Downloading: {item.url}")
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
