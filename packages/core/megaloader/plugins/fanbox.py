import logging
import os
import re

from collections.abc import Generator
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

import requests

from megaloader.item import DownloadItem
from megaloader.plugin import BasePlugin


logger = logging.getLogger(__name__)


class Fanbox(BasePlugin):
    """Extract content from Fanbox creator pages."""

    API_BASE = "https://api.fanbox.cc"

    def __init__(self, url: str, **options: Any) -> None:
        super().__init__(url, **options)
        self.creator_id = self._parse_creator_id(self.url)

    def _parse_creator_id(self, url: str) -> str:
        match = re.search(
            r"//(?:www\.)?([\w-]+)\.fanbox\.cc|fanbox\.cc/(?:@)?([\w-]+)", url
        )
        if not match:
            msg = f"Invalid Fanbox URL: {url}"
            raise ValueError(msg)
        return next(g for g in match.groups() if g)

    def _configure_session(self, session: requests.Session) -> None:
        session.headers.update(
            {
                "Origin": f"https://{self.creator_id}.fanbox.cc",
                "Referer": f"https://{self.creator_id}.fanbox.cc/",
            }
        )

        session_id = self.options.get("session_id") or os.getenv("FANBOX_SESSION_ID")
        if session_id:
            session.cookies.set("FANBOXSESSID", session_id, domain=".fanbox.cc")
            logger.debug("Using Fanbox session authentication")

    def extract(self) -> Generator[DownloadItem, None, None]:
        logger.debug("Starting Fanbox extraction for creator: %s", self.creator_id)

        seen_urls: set[str] = set()
        yield from self._extract_profile(seen_urls)
        yield from self._extract_posts(seen_urls)

    def _api_request(self, endpoint: str) -> Any:
        url = endpoint if endpoint.startswith("http") else self.API_BASE + endpoint
        response = self._get(url)
        return response.json().get("body")

    def _extract_profile(
        self, seen_urls: set[str]
    ) -> Generator[DownloadItem, None, None]:
        data = self._api_request(f"/creator.get?creatorId={self.creator_id}")
        if not data:
            return

        if icon_url := data.get("user", {}).get("iconUrl"):
            if icon_url not in seen_urls:
                seen_urls.add(icon_url)
                yield self._make_item(icon_url, f"avatar{Path(icon_url).suffix}", "profile")

        if cover_url := data.get("coverImageUrl"):
            if cover_url not in seen_urls:
                seen_urls.add(cover_url)
                yield self._make_item(cover_url, f"banner{Path(cover_url).suffix}", "profile")

    def _extract_posts(
        self, seen_urls: set[str]
    ) -> Generator[DownloadItem, None, None]:
        page_urls = self._api_request(
            f"/post.paginateCreator?creatorId={self.creator_id}"
        )
        if not page_urls:
            return

        for page_url in page_urls:
            if posts := self._api_request(page_url):
                for post in posts:
                    yield from self._extract_post(str(post["id"]), seen_urls)

    def _extract_post(
        self, post_id: str, seen_urls: set[str]
    ) -> Generator[DownloadItem, None, None]:
        info = self._api_request(f"/post.info?postId={post_id}")
        if not info:
            return

        title = info.get("title", f"post_{post_id}")
        subfolder = f"{post_id}_{title}"
        body = info.get("body", {})

        if not body:
            if cover_url := info.get("coverImageUrl"):
                if cover_url not in seen_urls:
                    seen_urls.add(cover_url)
                    yield self._make_item(cover_url, f"cover{Path(cover_url).suffix}", subfolder)
            return

        for img in body.get("imageMap", {}).values():
            if url := img.get("originalUrl"):
                if url not in seen_urls:
                    seen_urls.add(url)
                    filename = Path(unquote(urlparse(url).path)).name or "image.jpg"
                    yield self._make_item(url, filename, subfolder)

        for f in body.get("fileMap", {}).values():
            if url := f.get("url"):
                if url not in seen_urls:
                    seen_urls.add(url)
                    filename = f"{f.get('name')}.{f.get('extension')}"
                    yield self._make_item(url, filename, subfolder)

    def _make_item(self, url: str, filename: str, subfolder: str = "") -> DownloadItem:
        collection_name = f"{self.creator_id}_{subfolder}" if subfolder else self.creator_id
        return DownloadItem(
            download_url=url,
            filename=filename,
            collection_name=collection_name,
        )
