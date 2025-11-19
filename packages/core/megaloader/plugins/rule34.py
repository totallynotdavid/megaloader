import logging
import os
import xml.etree.ElementTree as ET

from collections.abc import Generator
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urljoin, urlparse

import requests

from bs4 import BeautifulSoup

from megaloader.plugin import BasePlugin, Item


logger = logging.getLogger(__name__)


class Rule34(BasePlugin):
    def __init__(self, url: str, **kwargs: Any) -> None:
        super().__init__(url, **kwargs)
        query = parse_qs(urlparse(url).query)
        self.post_id = query.get("id", [None])[0]
        self.tags = query.get("tags", [""])[0].split()

        if not self.post_id and not self.tags:
            msg = "URL must contain 'id' or 'tags'"
            raise ValueError(msg)

        self.api_key = os.getenv("RULE34_API_KEY")
        self.user_id = os.getenv("RULE34_USER_ID")

    def extract(self) -> Generator[Item, None, None]:
        if self.post_id:
            yield from self._export_single()
        elif self.api_key and self.user_id:
            yield from self._export_api()
        else:
            yield from self._export_scraper()

    def _export_single(self) -> Generator[Item, None, None]:
        url = f"https://rule34.xxx/index.php?page=post&s=view&id={self.post_id}"
        if resp := self._safe_get(url):
            soup = BeautifulSoup(resp.text, "html.parser")
            if file_url := self._extract_media_url(soup):
                yield self._create_item(file_url, f"post_{self.post_id}", self.post_id)

    def _export_api(self) -> Generator[Item, None, None]:
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
            resp = self._safe_get("https://api.rule34.xxx/index.php", params)
            if not resp:
                break

            try:
                posts = list(ET.fromstring(resp.content).iter("post"))
            except ET.ParseError:
                break

            if not posts:
                break
            for post in posts:
                if url := post.get("file_url"):
                    yield self._create_item(url, album_title, post.get("id"))
            page += 1

    def _export_scraper(self) -> Generator[Item, None, None]:
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
            resp = self._safe_get("https://rule34.xxx/index.php", params)
            if not resp:
                break

            links = BeautifulSoup(resp.text, "html.parser").select(
                "div.image-list span.thumb > a"
            )
            if not links:
                break

            for link in links:
                href = link.get("href")
                if not href or href in seen_urls:
                    continue
                seen_urls.add(href)

                href_str = str(href)
                post_resp = self._safe_get(urljoin("https://rule34.xxx/", href_str))
                if post_resp and (
                    file_url := self._extract_media_url(
                        BeautifulSoup(post_resp.text, "html.parser")
                    )
                ):
                    yield self._create_item(file_url, album_title)
            pid += 42  # Rule34 pagination offset

    def _safe_get(
        self, url: str, params: dict[str, Any] | None = None
    ) -> requests.Response | None:
        try:
            r = self.session.get(url, params=params, timeout=30)
            r.raise_for_status()
            return r
        except requests.RequestException:
            return None

    def _extract_media_url(self, soup: BeautifulSoup) -> str | None:
        # Original image link
        for link in soup.find_all("a"):
            if "Original image" in str(link.string):
                href = link.get("href")
                return str(href) if href else None
        # Video/Image fallback
        if v := soup.select_one("video > source"):
            src = v.get("src")
            return str(src) if src else None
        if i := soup.select_one("img#image"):
            src = i.get("src")
            return str(src) if src else None
        return None

    def _create_item(self, url: str, album: str, post_id: str | None = None) -> Item:
        url = f"https:{url}" if url.startswith("//") else url
        return Item(
            url=url,
            filename=Path(unquote(urlparse(url).path)).name,
            album=album,
            id=post_id,
        )
