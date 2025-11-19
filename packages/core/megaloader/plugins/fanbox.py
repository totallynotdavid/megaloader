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
        self.creator_id = self._parse_creator_id(url)
        super().__init__(url, **options)

    def _parse_creator_id(self, url: str) -> str:
        match = re.search(
            r"//(?:www\.)?([\w-]+)\.fanbox\.cc|fanbox\.cc/(?:@)?([\w-]+)", url
        )
        if not match:
            raise ValueError(f"Invalid Fanbox URL: {url}")
        return next(g for g in match.groups() if g)

    def _configure_session(self, session: requests.Session) -> None:
        session.headers.update({
            "Origin": f"https://{self.creator_id}.fanbox.cc",
            "Referer": f"https://{self.creator_id}.fanbox.cc/",
        })
        
        # Credentials: kwargs > env var
        session_id = self.options.get("session_id") or os.getenv("FANBOX_SESSION_ID")
        if session_id:
            session.cookies.set("FANBOXSESSID", session_id, domain=".fanbox.cc")
            logger.debug("Using Fanbox session authentication")

    def extract(self) -> Generator[DownloadItem, None, None]:
        logger.debug("Starting Fanbox extraction for creator: %s", self.creator_id)
        
        seen_urls: set[str] = set()
        
        # Profile assets
        yield from self._extract_profile(seen_urls)
        
        # All posts
        yield from self._extract_posts(seen_urls)

    def _api_request(self, endpoint: str) -> Any:
        """Make API request and return body or None on error."""
        url = endpoint if endpoint.startswith("http") else self.API_BASE + endpoint
        
        try:
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 403:
                logger.warning("Access forbidden (auth required?): %s", url)
                return None
            
            response.raise_for_status()
            return response.json().get("body")
        except Exception:
            logger.debug("API request failed: %s", url, exc_info=True)
            return None

    def _extract_profile(self, seen_urls: set[str]) -> Generator[DownloadItem, None, None]:
        """Extract profile images (avatar, banner)."""
        data = self._api_request(f"/creator.get?creatorId={self.creator_id}")
        if not data:
            return

        # Avatar
        if icon_url := data.get("user", {}).get("iconUrl"):
            yield from self._create_item(
                icon_url, f"avatar{Path(icon_url).suffix}", seen_urls, "profile"
            )

        # Banner
        if cover_url := data.get("coverImageUrl"):
            yield from self._create_item(
                cover_url, f"banner{Path(cover_url).suffix}", seen_urls, "profile"
            )

    def _extract_posts(self, seen_urls: set[str]) -> Generator[DownloadItem, None, None]:
        """Extract all posts from creator."""
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
        """Extract files from a single post."""
        info = self._api_request(f"/post.info?postId={post_id}")
        if not info:
            return

        title = info.get("title", f"post_{post_id}")
        subfolder = f"{post_id}_{title}"
        body = info.get("body", {})

        # Cover image (for posts without body)
        if not body:
            if cover_url := info.get("coverImageUrl"):
                yield from self._create_item(
                    cover_url, f"cover{Path(cover_url).suffix}", seen_urls, subfolder
                )
            return

        # Images
        for img in body.get("imageMap", {}).values():
            if url := img.get("originalUrl"):
                filename = Path(unquote(urlparse(url).path)).name or "image.jpg"
                yield from self._create_item(url, filename, seen_urls, subfolder)

        # File attachments
        for f in body.get("fileMap", {}).values():
            if url := f.get("url"):
                filename = f"{f.get('name')}.{f.get('extension')}"
                yield from self._create_item(url, filename, seen_urls, subfolder)

    def _create_item(
        self,
        url: str,
        filename: str,
        seen_urls: set[str],
        subfolder: str = "",
    ) -> Generator[DownloadItem, None, None]:
        """Create item if not already seen."""
        if url in seen_urls:
            return
        
        seen_urls.add(url)
        
        full_filename = str(Path(subfolder) / filename) if subfolder else filename
        
        yield DownloadItem(
            download_url=url,
            filename=full_filename,
            collection_name=self.creator_id,
        )
