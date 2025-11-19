import logging
import os
import re

from collections.abc import Generator
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

import requests

from megaloader.plugin import BasePlugin, Item


logger = logging.getLogger(__name__)


class Fanbox(BasePlugin):
    BASE_API_URL = "https://api.fanbox.cc"
    PROFILE_SUBFOLDER = "profile"

    def __init__(self, url: str, **kwargs: Any) -> None:
        self.creator_id = self._get_creator_id(url)
        super().__init__(url, **kwargs)

    def _create_session(self) -> requests.Session:
        """Override to add creator-specific headers."""
        session = super()._create_session()
        session.headers.update(
            {
                "Origin": f"https://{self.creator_id}.fanbox.cc",
                "Referer": f"https://{self.creator_id}.fanbox.cc/",
            }
        )
        if sess_id := os.getenv("FANBOX_SESSION_ID"):
            session.cookies.set("FANBOXSESSID", sess_id, domain=".fanbox.cc")
        return session

    def _get_creator_id(self, url: str) -> str:
        match = re.search(
            r"//(?:www\.)?([\w-]+)\.fanbox\.cc|fanbox\.cc/(?:@)?([\w-]+)", url
        )
        if not match:
            msg = f"Invalid Fanbox URL: {url}"
            raise ValueError(msg)
        return next(g for g in match.groups() if g)

    def _api_request(self, endpoint: str) -> Any:
        url = endpoint if endpoint.startswith("http") else self.BASE_API_URL + endpoint
        try:
            response = self.session.get(url, timeout=30)
            if response.status_code == 403:
                logger.warning("Access forbidden: %s", url)
                return None
            response.raise_for_status()
            return response.json().get("body")
        except Exception:
            logger.exception("API request failed for %s", url)
            return None

    def _sanitize_filename(self, filename: str) -> str:
        sanitized = re.sub(r'[<>:"/\\|?*]', "_", filename).strip()
        return sanitized[:150] if sanitized else "unnamed"

    def extract(self) -> Generator[Item, None, None]:
        logger.info("Starting Fanbox export for creator: %s", self.creator_id)
        seen_urls = set()
        yield from self._process_profile(seen_urls)
        yield from self._process_posts(seen_urls)

    def _create_item(
        self, url: str, filename: str, seen_urls: set, subfolder: str = ""
    ) -> Generator[Item, None, None]:
        if url in seen_urls:
            return
        seen_urls.add(url)

        sanitized_name = self._sanitize_filename(filename)
        full_name = (
            str(Path(subfolder) / sanitized_name) if subfolder else sanitized_name
        )

        yield Item(url=url, filename=full_name, album=self.creator_id)

    def _process_profile(self, seen_urls: set) -> Generator[Item, None, None]:
        data = self._api_request(f"/creator.get?creatorId={self.creator_id}")
        if not data:
            return

        if icon := data.get("user", {}).get("iconUrl"):
            yield from self._create_item(
                icon, f"avatar{Path(icon).suffix}", seen_urls, self.PROFILE_SUBFOLDER
            )

        if cover := data.get("coverImageUrl"):
            yield from self._create_item(
                cover, f"banner{Path(cover).suffix}", seen_urls, self.PROFILE_SUBFOLDER
            )

    def _process_posts(self, seen_urls: set) -> Generator[Item, None, None]:
        page_urls = self._api_request(
            f"/post.paginateCreator?creatorId={self.creator_id}"
        )
        if not page_urls:
            return

        for page_url in page_urls:
            if posts := self._api_request(page_url):
                for post in posts:
                    yield from self._process_single_post(str(post["id"]), seen_urls)

    def _process_single_post(
        self, post_id: str, seen_urls: set
    ) -> Generator[Item, None, None]:
        info = self._api_request(f"/post.info?postId={post_id}")
        if not info:
            return

        title = self._sanitize_filename(info.get("title", f"post_{post_id}"))
        subfolder = f"{post_id}_{title}"
        body = info.get("body", {})

        if not body:
            if cover := info.get("coverImageUrl"):
                yield from self._create_item(
                    cover, f"cover{Path(cover).suffix}", seen_urls, subfolder
                )
            return

        for img in body.get("imageMap", {}).values():
            if url := img.get("originalUrl"):
                fname = Path(unquote(urlparse(url).path)).name or "image.jpg"
                yield from self._create_item(url, fname, seen_urls, subfolder)

        for f in body.get("fileMap", {}).values():
            if url := f.get("url"):
                fname = f"{f.get('name')}.{f.get('extension')}"
                yield from self._create_item(url, fname, seen_urls, subfolder)
