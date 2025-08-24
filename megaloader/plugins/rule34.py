import logging
import os
import xml.etree.ElementTree as ET

from collections.abc import Generator
from typing import Any, Optional
from urllib.parse import parse_qs, unquote, urljoin, urlparse

import requests

from bs4 import BeautifulSoup

from megaloader.http import download_file as http_download
from megaloader.plugin import BasePlugin, Item


logger = logging.getLogger(__name__)


class Rule34(BasePlugin):
    """
    This plugin supports two operational modes:

    Via API (recommended): Uses the official API. It requires the following environment variables:
    RULE34_API_KEY and RULE34_USER_ID. Get them at https://rule34.xxx/index.php?page=account&s=options.
    You have to click on 'Generate New Key' the first time you use it.

    Scraping mode: Used as fallback when API credentials are missing.
    Scrapes the website directly and is less reliable, but requires no setup.

    Supported URL Formats
    1. Single Post: https://rule34.xxx/index.php?page=post&s=view&id={postId}
    2. Tag Gallery: https://rule34.xxx/index.php?page=post&s=list&tags={tags}
    """

    def __init__(self, url: str, **kwargs: Any) -> None:
        super().__init__(url, **kwargs)

        query = parse_qs(urlparse(url).query)
        self.post_id = query.get("id", [None])[0]

        if not self.post_id:
            tags_str = query.get("tags", [""])[0]
            self.tags = [
                tag.strip() for tag in tags_str.replace("+", " ").split() if tag.strip()
            ]
        else:
            self.tags = []

        if not self.post_id and not self.tags:
            raise ValueError("URL must contain 'id' or 'tags' parameter")

        self.session = requests.Session()
        self.session.headers["User-Agent"] = "Mozilla/5.0 (compatible)"

        self.api_key = os.getenv("RULE34_API_KEY")
        self.user_id = os.getenv("RULE34_USER_ID")
        self.use_api = bool(self.api_key and self.user_id)

    def _get_with_timeout(
        self, url: str, params: Optional[dict] = None
    ) -> Optional[requests.Response]:
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            logger.warning(f"Request failed for {url}: {e}")
            return None

    def _normalize_url(self, url: str) -> str:
        return f"https:{url}" if url.startswith("//") else url

    def _extract_media_url(self, soup: BeautifulSoup) -> Optional[str]:
        # Try original image link first (best quality)
        original_link = soup.find("a", string=lambda t: t and "Original image" in t)
        if original_link and original_link.get("href"):
            return original_link["href"]

        # Try video source for video posts
        video_source = soup.select_one("video > source")
        if video_source and video_source.get("src"):
            return video_source["src"]

        # Fallback to main image
        img_tag = soup.select_one("img#image")
        if img_tag and img_tag.get("src"):
            return img_tag["src"]

        return None

    def _create_item(
        self, file_url: str, album_title: str, file_id: Optional[str] = None
    ) -> Item:
        """Create Item with normalized URL and extracted filename."""
        file_url = self._normalize_url(file_url)
        filename = os.path.basename(unquote(urlparse(file_url).path))
        return Item(
            url=file_url, filename=filename, album_title=album_title, file_id=file_id
        )

    def export(self) -> Generator[Item, None, None]:
        if self.post_id:
            yield from self._export_single()
        elif self.use_api:
            yield from self._export_api()
        else:
            yield from self._export_scraper()

    def _export_single(self) -> Generator[Item, None, None]:
        """Export single post by ID."""
        url = f"https://rule34.xxx/index.php?page=post&s=view&id={self.post_id}"
        response = self._get_with_timeout(url)
        if not response:
            return

        soup = BeautifulSoup(response.text, "html.parser")
        file_url = self._extract_media_url(soup)

        if file_url:
            yield self._create_item(file_url, f"post_{self.post_id}", self.post_id)

    def _export_api(self) -> Generator[Item, None, None]:
        logger.info(f"Using API mode for tags: {' '.join(self.tags)}")
        album_title = "_".join(sorted(self.tags))
        page = 0

        while True:
            params = {
                "page": "dapi",
                "s": "post",
                "q": "index",
                "tags": " ".join(self.tags),
                "pid": page,
                "limit": 1000,
                "api_key": self.api_key,
                "user_id": self.user_id,
            }

            response = self._get_with_timeout(
                "https://api.rule34.xxx/index.php", params
            )
            if not response:
                break

            try:
                root = ET.fromstring(response.content)
            except ET.ParseError as e:
                logger.error(f"Failed to parse API response: {e}")
                break

            posts = list(root.iter("post"))
            if not posts:
                break

            for post in posts:
                file_url = post.get("file_url")
                if file_url:
                    yield self._create_item(file_url, album_title, post.get("id"))
            page += 1

    def _export_scraper(self) -> Generator[Item, None, None]:
        logger.info(f"Using scraper mode for tags: {' '.join(self.tags)}")
        album_title = "_".join(sorted(self.tags))
        pid = 0
        seen_urls = set()

        while True:
            params = {
                "page": "post",
                "s": "list",
                "tags": " ".join(self.tags),
                "pid": pid,
            }

            response = self._get_with_timeout("https://rule34.xxx/index.php", params)
            if not response:
                break

            soup = BeautifulSoup(response.text, "html.parser")
            post_links = soup.select("div.image-list span.thumb > a")
            if not post_links:
                break

            for link in post_links:
                href = link.get("href")
                if not href or href in seen_urls:
                    continue
                seen_urls.add(href)

                post_url = urljoin("https://rule34.xxx/index.php", href)
                post_response = self._get_with_timeout(post_url)
                if not post_response:
                    continue

                post_soup = BeautifulSoup(post_response.text, "html.parser")
                file_url = self._extract_media_url(post_soup)

                if file_url:
                    yield self._create_item(file_url, album_title)

            pid += 42

    def download_file(self, item: Item, output_dir: str) -> bool:
        result = http_download(item.url, output_dir, item.filename)
        return result is not None
