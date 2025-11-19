import logging
import os
import xml.etree.ElementTree as ET
from collections.abc import Generator
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from megaloader.item import DownloadItem
from megaloader.plugin import BasePlugin

logger = logging.getLogger(__name__)


class Rule34(BasePlugin):
    """Extract posts from Rule34."""

    def __init__(self, url: str, **options: Any) -> None:
        super().__init__(url, **options)
        query = parse_qs(urlparse(url).query)
        self.post_id = query.get("id", [None])[0]
        self.tags = query.get("tags", [""])[0].split()

        if not self.post_id and not self.tags:
            raise ValueError("URL must contain 'id' or 'tags' parameter")

        # Credentials: kwargs > env vars
        self.api_key = self.options.get("api_key") or os.getenv("RULE34_API_KEY")
        self.user_id = self.options.get("user_id") or os.getenv("RULE34_USER_ID")

    def extract(self) -> Generator[DownloadItem, None, None]:
        if self.post_id:
            yield from self._extract_single_post()
        elif self.api_key and self.user_id:
            logger.debug("Using API extraction")
            yield from self._extract_via_api()
        else:
            logger.debug("Using web scraping (slower, set API credentials for better performance)")
            yield from self._extract_via_scraper()

    def _extract_single_post(self) -> Generator[DownloadItem, None, None]:
        """Extract a single post by ID."""
        url = f"https://rule34.xxx/index.php?page=post&s=view&id={self.post_id}"
        
        if response := self._safe_get(url):
            soup = BeautifulSoup(response.text, "html.parser")
            if media_url := self._extract_media_url(soup):
                yield self._create_item(media_url, f"post_{self.post_id}", self.post_id)

    def _extract_via_api(self) -> Generator[DownloadItem, None, None]:
        """Extract using official API (faster, more reliable)."""
        collection_name = "_".join(sorted(self.tags))
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
            
            response = self._safe_get("https://api.rule34.xxx/index.php", params)
            if not response:
                break

            try:
                root = ET.fromstring(response.content)
                posts = list(root.iter("post"))
            except ET.ParseError:
                break

            if not posts:
                break

            for post in posts:
                if url := post.get("file_url"):
                    yield self._create_item(url, collection_name, post.get("id"))

            page += 1

    def _extract_via_scraper(self) -> Generator[DownloadItem, None, None]:
        """Extract by scraping web pages (fallback method)."""
        collection_name = "_".join(sorted(self.tags))
        pid = 0
        seen_urls = set()

        while True:
            params = {
                "page": "post",
                "s": "list",
                "tags": " ".join(self.tags),
                "pid": pid,
            }
            
            response = self._safe_get("https://rule34.xxx/index.php", params)
            if not response:
                break

            soup = BeautifulSoup(response.text, "html.parser")
            links = soup.select("div.image-list span.thumb > a")
            
            if not links:
                break

            for link in links:
                href = link.get("href")
                if not href or href in seen_urls:
                    continue
                
                seen_urls.add(href)
                full_url = urljoin("https://rule34.xxx/", str(href))
                
                if post_response := self._safe_get(full_url):
                    soup = BeautifulSoup(post_response.text, "html.parser")
                    if media_url := self._extract_media_url(soup):
                        yield self._create_item(media_url, collection_name)

            pid += 42  # Rule34 pagination increment

    def _safe_get(
        self, url: str, params: dict[str, Any] | None = None
    ) -> requests.Response | None:
        """Make GET request with error handling."""
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response
        except requests.RequestException:
            logger.debug("Request failed: %s", url, exc_info=True)
            return None

    def _extract_media_url(self, soup: BeautifulSoup) -> str | None:
        """Extract media URL from post page."""
        # Original image link
        for link in soup.find_all("a"):
            if "Original image" in str(link.string):
                if href := link.get("href"):
                    return str(href)

        # Video source
        if video := soup.select_one("video > source"):
            if src := video.get("src"):
                return str(src)

        # Image fallback
        if img := soup.select_one("img#image"):
            if src := img.get("src"):
                return str(src)

        return None

    def _create_item(
        self, url: str, collection_name: str, post_id: str | None = None
    ) -> DownloadItem:
        """Create DownloadItem from URL."""
        url = f"https:{url}" if url.startswith("//") else url
        
        return DownloadItem(
            download_url=url,
            filename=Path(unquote(urlparse(url).path)).name,
            collection_name=collection_name,
            source_id=post_id,
        )
