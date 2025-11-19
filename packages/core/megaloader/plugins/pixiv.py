import logging
import os
import re

from collections.abc import Generator
from pathlib import Path
from typing import Any

import requests

from megaloader.item import DownloadItem
from megaloader.plugin import BasePlugin


logger = logging.getLogger(__name__)


class Pixiv(BasePlugin):
    """Extract artworks from Pixiv."""

    SITE_BASE = "https://www.pixiv.net"

    def __init__(self, url: str, **options: Any) -> None:
        super().__init__(url, **options)
        self.content_id, self.is_artwork = self._parse_url()

    def _parse_url(self) -> tuple[str, bool]:
        """Determine if URL is artwork or user profile."""
        if match := re.search(r"artworks/(\d+)", self.url):
            return match.group(1), True

        if match := re.search(r"users/(\d+)|member\.php\?id=(\d+)", self.url):
            return match.group(1) or match.group(2), False

        msg = "Invalid Pixiv URL"
        raise ValueError(msg)

    def _configure_session(self, session: requests.Session) -> None:
        session.headers["Referer"] = f"{self.SITE_BASE}/"

        # Credentials: kwargs > env var
        session_id = self.options.get("session_id") or os.getenv("PIXIV_PHPSESSID")
        if session_id:
            session.cookies.set("PHPSESSID", session_id, domain=".pixiv.net")
            logger.debug("Using Pixiv session authentication")

    def extract(self) -> Generator[DownloadItem, None, None]:
        if self.is_artwork:
            yield from self._extract_artwork(self.content_id)
        else:
            yield from self._extract_user(self.content_id)

    def _api_request(self, endpoint: str, params: dict[str, Any] | None = None) -> Any:
        """Make API request and return body or None."""
        try:
            response = self.session.get(
                f"{self.SITE_BASE}/ajax{endpoint}",
                params=params,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            return data.get("body") if not data.get("error") else None
        except (requests.RequestException, ValueError):
            logger.debug("Pixiv API error: %s", endpoint, exc_info=True)
            return None

    def _extract_artwork(
        self,
        artwork_id: str,
        collection_name: str | None = None,
    ) -> Generator[DownloadItem, None, None]:
        """Extract images from a single artwork."""
        pages = self._api_request(f"/illust/{artwork_id}/pages")

        # Fallback for single-page artworks
        if not pages:
            info = self._api_request(f"/illust/{artwork_id}")
            if info and (url := info.get("urls", {}).get("original")):
                pages = [{"urls": {"original": url}}]
            else:
                return

        if not collection_name:
            info = self._api_request(f"/illust/{artwork_id}")
            username = info.get("userName", "unknown") if info else "artwork"
            collection_name = f"{username}_{artwork_id}"

        for page_num, page in enumerate(pages):
            url = page.get("urls", {}).get("original")
            if not url:
                continue

            ext = Path(url).suffix
            filename = f"{artwork_id}_p{page_num}{ext}"

            yield DownloadItem(
                download_url=url,
                filename=filename,
                collection_name=collection_name,
                headers={"Referer": f"{self.SITE_BASE}/artworks/{artwork_id}"},
            )

    def _extract_user(self, user_id: str) -> Generator[DownloadItem, None, None]:
        """Extract all works from a user."""
        profile = self._api_request(f"/user/{user_id}", params={"full": 1})
        if not profile:
            return

        username = profile.get("name", user_id)
        collection_name = f"{user_id}_{username}"

        # Profile images
        if avatar_url := profile.get("imageBig"):
            yield DownloadItem(
                download_url=avatar_url,
                filename=f"avatar{Path(avatar_url).suffix}",
                collection_name=collection_name,
            )

        if (bg := profile.get("background")) and (bg_url := bg.get("url")):
            yield DownloadItem(
                download_url=bg_url,
                filename=f"cover{Path(bg_url).suffix}",
                collection_name=collection_name,
            )

        # All artworks
        all_works = self._api_request(f"/user/{user_id}/profile/all") or {}
        work_ids = list(all_works.get("illusts", {}).keys()) + list(
            all_works.get("manga", {}).keys()
        )

        for work_id in work_ids:
            yield from self._extract_artwork(work_id, collection_name)
