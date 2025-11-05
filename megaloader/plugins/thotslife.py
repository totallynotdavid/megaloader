import logging
import re

from collections.abc import Generator
from pathlib import Path
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
            },
        )

    def _sanitize_filename(self, filename: str) -> str:
        return self._FILENAME_SANITIZE_RE.sub("_", filename).strip()

    def export(self) -> Generator[Item, None, None]:
        """
        Fetches the page and yields all found media items (videos and images).
        """
        logger.info("Processing Thotslife URL: %s", self.url)

        try:
            response = self.session.get(self.url, timeout=30)
            response.raise_for_status()
        except requests.RequestException:
            logger.exception("Failed to fetch page %s", self.url)
            return

        soup = BeautifulSoup(response.text, "html.parser")

        title_tag = soup.find("h1", class_="entry-title")
        album_title = (
            self._sanitize_filename(title_tag.text.strip())
            if title_tag
            else "thotslife_album"
        )
        logger.info("Found post: %s", album_title)

        article_body_element = soup.find("div", itemprop="articleBody")

        if not isinstance(article_body_element, Tag):
            logger.warning("Could not find article body on page: %s", self.url)
            return

        article_body: Tag = article_body_element

        media_found = 0
        seen_urls: set[str] = set()

        for item in self._find_videos(article_body, album_title, seen_urls):
            yield item
            media_found += 1
        for item in self._find_images(article_body, album_title, seen_urls):
            yield item
            media_found += 1

        if media_found == 0:
            logger.warning("No media found on page: %s", self.url)

    def _find_videos(
        self,
        article_body: Tag,
        album_title: str,
        seen_urls: set[str],
    ) -> Generator[Item, None, None]:
        video_sources = article_body.select("video > source[src]")
        for source in video_sources:
            video_url = source.get("src")

            if isinstance(video_url, str) and video_url not in seen_urls:
                seen_urls.add(video_url)
                filename = Path(unquote(urlparse(video_url).path)).name

                if not filename:
                    filename = f"{album_title}.mp4"

                logger.debug("Found video: %s", filename)
                yield Item(url=video_url, filename=filename, album_title=album_title)

    def _find_images(
        self,
        article_body: Tag,
        album_title: str,
        seen_urls: set[str],
    ) -> Generator[Item, None, None]:
        # Find images (via data-src)
        image_tags = article_body.select("img[data-src]")
        for img in image_tags:
            image_url = img.get("data-src")

            if isinstance(image_url, str) and image_url not in seen_urls:
                # Skip placeholder SVG images
                if image_url.startswith("data:image/svg+xml"):
                    continue

                seen_urls.add(image_url)

                filename = Path(unquote(urlparse(image_url).path)).name
                if not filename:
                    ext = Path(urlparse(image_url).path).suffix or ".jpg"
                    filename = f"image_{len(seen_urls)}{ext}"

                logger.debug("Found image: %s", filename)
                yield Item(url=image_url, filename=filename, album_title=album_title)

    def download_file(self, item: Item, output_dir: str) -> bool:
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        output_path = Path(output_dir) / item.filename

        if output_path.exists():
            logger.info("File already exists: %s", item.filename)
            return True

        is_video = item.filename.lower().endswith(".mp4")

        try:
            logger.debug("Downloading: %s", item.url)
            with self.session.get(
                item.url,
                stream=True,
                timeout=360,
                allow_redirects=True,
                verify=not is_video,
            ) as response:
                response.raise_for_status()
                with Path(output_path).open("wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
            logger.info("Downloaded: %s", item.filename)
        except requests.RequestException:
            logger.exception("Download failed for %s", item.filename)
            if output_path.exists():
                output_path.unlink()
            return False
        else:
            return True
