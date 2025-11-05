import logging
import os
import re

from collections.abc import Generator
from typing import Any
from urllib.parse import unquote, urljoin, urlparse

import requests

from bs4 import BeautifulSoup

from megaloader.plugin import BasePlugin, Item


logger = logging.getLogger(__name__)


class Fapello(BasePlugin):
    # Regex to remove thumbnail suffixes like _300px from image URLs
    _THUMBNAIL_SUFFIX_RE = re.compile(r"_\d+px(\.(?:jpg|jpeg|png|mp4))$", re.IGNORECASE)

    def __init__(self, url: str, **kwargs: Any) -> None:
        super().__init__(url, **kwargs)
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Referer": "https://fapello.com/",
            },
        )
        self.model = self._get_model_from_url(url)

    def _get_model_from_url(self, url: str) -> str:
        """Extracts the model name from a Fapello URL."""
        match = re.search(r"fapello\.com/([a-zA-Z0-9_\-~\.]+)", url)
        if not match:
            msg = "Invalid Fapello URL provided. Could not find model name."
            raise ValueError(msg)
        model_name = match.group(1).split("/")[0]
        if not model_name:
            msg = "Invalid Fapello URL provided. Model name is empty."
            raise ValueError(msg)
        logger.debug(f"Found model name: {model_name}")
        return model_name

    def _get_full_res_url(self, thumb_url: str) -> str:
        """Converts a thumbnail URL to a full-resolution URL."""
        return self._THUMBNAIL_SUFFIX_RE.sub(r"\1", thumb_url)

    def export(self) -> Generator[Item, None, None]:
        """
        Scrapes all media from a model's profile by iterating through their
        AJAX-loaded pages of thumbnails.
        """
        logger.info(f"Starting export for Fapello model: {self.model}")
        page_num = 1
        seen_urls = set()

        while True:
            ajax_url = f"https://fapello.com/ajax/model/{self.model}/page-{page_num}/"
            logger.debug(f"Fetching page: {ajax_url}")

            try:
                response = self.session.get(ajax_url, timeout=30)
                response.raise_for_status()
            except requests.RequestException as e:
                logger.exception(
                    f"Failed to fetch page {page_num} for model {self.model}: {e}",
                )
                break

            content = response.text.strip()
            if not content:
                logger.info("Reached the last page of content (empty response).")
                break

            soup = BeautifulSoup(content, "html.parser")
            # Find all img tags within links, as they are the media thumbnails
            thumb_elements = soup.select('a > div > img[src*="/content/"]')

            if not thumb_elements:
                if page_num == 1:
                    logger.warning(
                        f"No media found on the first page for model: {self.model}. The model may not exist or has no content.",
                    )
                else:
                    logger.info("Reached the last page of content (no media found).")
                break

            logger.info(f"Found {len(thumb_elements)} media items on page {page_num}")

            for thumb_img in thumb_elements:
                thumb_url = urljoin("https://fapello.com/", str(thumb_img["src"]))
                full_res_url = self._get_full_res_url(thumb_url)

                if full_res_url in seen_urls:
                    continue
                seen_urls.add(full_res_url)

                filename = os.path.basename(unquote(urlparse(full_res_url).path))
                yield Item(url=full_res_url, filename=filename, album_title=self.model)
            page_num += 1

    def download_file(self, item: Item, output_dir: str) -> bool:
        """Downloads a single file from Fapello."""
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, item.filename)

        if os.path.exists(output_path):
            logger.info(f"File already exists: {item.filename}")
            return True

        try:
            logger.debug(f"Downloading: {item.url}")
            with self.session.get(item.url, stream=True, timeout=180) as response:
                response.raise_for_status()
                with open(output_path, "wb") as f:
                    f.writelines(response.iter_content(chunk_size=8192))
            logger.info(f"Downloaded: {item.filename}")
            return True
        except requests.RequestException as e:
            logger.exception(f"Download failed for {item.filename}: {e}")
            if os.path.exists(output_path):
                os.remove(output_path)
            return False
