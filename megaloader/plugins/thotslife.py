import logging
import os
import re

from collections.abc import Generator
from typing import Any
from urllib.parse import unquote, urlparse

import requests

from bs4 import BeautifulSoup, Tag

from megaloader.plugin import BasePlugin, Item


logger = logging.getLogger(__name__)


class Thotslife(BasePlugin):
    _FILENAME_SANITIZE_RE = re.compile(r'[<>:"/\|?*]')

    def __init__(self, url: str, **kwargs: Any) -> None:
        super().__init__(url, **kwargs)
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "https://thotslife.com/",
            }
        )

    def _sanitize_filename(self, filename: str) -> str:
        return self._FILENAME_SANITIZE_RE.sub("_", filename).strip()

    def export(self) -> Generator[Item, None, None]:
        """
        Fetches the page and yields all found media items (videos and images).
        """
        logger.info(f"Processing Thotslife URL: {self.url}")

        try:
            response = self.session.get(self.url, timeout=30)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Failed to fetch page {self.url}: {e}")
            return

        soup = BeautifulSoup(response.text, "html.parser")

        title_tag = soup.find("h1", class_="entry-title")
        album_title = (
            self._sanitize_filename(title_tag.text.strip())
            if title_tag
            else "thotslife_album"
        )
        logger.info(f"Found post: {album_title}")

        article_body_element = soup.find("div", itemprop="articleBody")

        if not isinstance(article_body_element, Tag):
            logger.warning(f"Could not find article body on page: {self.url}")
            return

        article_body: Tag = article_body_element

        media_found = 0
        seen_urls = set()

        # Find videos
        video_sources = article_body.select("video > source[src]")
        for source in video_sources:
            video_url = source.get("src")

            if isinstance(video_url, str) and video_url not in seen_urls:
                seen_urls.add(video_url)
                filename = os.path.basename(unquote(urlparse(video_url).path))

                if not filename:
                    filename = f"{album_title}.mp4"

                logger.debug(f"Found video: {filename}")
                yield Item(url=video_url, filename=filename, album_title=album_title)
                media_found += 1

        # Find images (via data-src)
        image_tags = article_body.select("img[data-src]")
        for img in image_tags:
            image_url = img.get("data-src")

            if isinstance(image_url, str) and image_url not in seen_urls:
                # Skip placeholder SVG images
                if image_url.startswith("data:image/svg+xml"):
                    continue

                seen_urls.add(image_url)

                filename = os.path.basename(unquote(urlparse(image_url).path))
                if not filename:
                    ext = os.path.splitext(urlparse(image_url).path)[1] or ".jpg"
                    filename = f"image_{len(seen_urls)}{ext}"

                logger.debug(f"Found image: {filename}")
                yield Item(url=image_url, filename=filename, album_title=album_title)
                media_found += 1

        if media_found == 0:
            logger.warning(f"No media found on page: {self.url}")

    def download_file(self, item: Item, output_dir: str) -> bool:
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, item.filename)

        if os.path.exists(output_path):
            logger.info(f"File already exists: {item.filename}")
            return True

        is_video = item.filename.lower().endswith(".mp4")

        try:
            logger.debug(f"Downloading: {item.url}")
            with self.session.get(
                item.url,
                stream=True,
                timeout=360,
                allow_redirects=True,
                verify=not is_video,
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
