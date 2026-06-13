import logging
import os
import re

from collections.abc import Generator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from megaloader.error_policy import raise_extraction_error
from megaloader.fetcher import Cookie, Fetcher, Request, SessionConfig
from megaloader.item import DownloadItem
from megaloader.plugin import BasePlugin


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Artwork:
    artwork_id: str


@dataclass(frozen=True)
class User:
    user_id: str


Target = Artwork | User


def parse_target(url: str) -> Target:
    """Classify a Pixiv URL as a single artwork or a user gallery."""
    if match := re.search(r"artworks/(\d+)", url):
        return Artwork(match.group(1))

    if match := re.search(r"users/(\d+)|member\.php\?id=(\d+)", url):
        return User(match.group(1) or match.group(2))

    msg = "Invalid Pixiv URL"
    raise ValueError(msg)


class Pixiv(BasePlugin):
    """Extract artworks from Pixiv."""

    SITE_BASE = "https://www.pixiv.net"

    def __init__(self, url: str, **options: Any) -> None:
        super().__init__(url, **options)
        self.target = parse_target(self.url)

    def session_config(self) -> SessionConfig:
        cookies: tuple[Cookie, ...] = ()
        session_id = self.options.get("session_id") or os.getenv("PIXIV_PHPSESSID")
        if session_id:
            cookies = (Cookie("PHPSESSID", session_id, ".pixiv.net"),)
            logger.debug("Using Pixiv session authentication")

        return SessionConfig(headers={"Referer": f"{self.SITE_BASE}/"}, cookies=cookies)

    def extract(self, fetch: Fetcher) -> Generator[DownloadItem, None, None]:
        if isinstance(self.target, Artwork):
            yield from self._extract_artwork(fetch, self.target.artwork_id)
        else:
            yield from self._extract_user(fetch, self.target.user_id)

    def _api_request(
        self, fetch: Fetcher, endpoint: str, params: dict[str, Any] | None = None
    ) -> Any:
        request_url = f"{self.SITE_BASE}/ajax{endpoint}"
        response = fetch(Request(request_url, params=params))
        data = response.json()

        if data.get("error"):
            msg = data.get("message") or "Pixiv API returned an error"
            raise_extraction_error(
                msg,
                source="pixiv",
                url=request_url,
                provider_status=str(data.get("error")),
            )

        return data.get("body")

    def _extract_artwork(
        self,
        fetch: Fetcher,
        artwork_id: str,
        collection_name: str | None = None,
    ) -> Generator[DownloadItem, None, None]:
        pages = self._api_request(fetch, f"/illust/{artwork_id}/pages")

        info: Any = None

        if not pages:
            info = self._api_request(fetch, f"/illust/{artwork_id}")
            if info and (url := info.get("urls", {}).get("original")):
                pages = [{"urls": {"original": url}}]
            else:
                return

        if not collection_name:
            info = info or self._api_request(fetch, f"/illust/{artwork_id}")
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

    def _extract_user(
        self, fetch: Fetcher, user_id: str
    ) -> Generator[DownloadItem, None, None]:
        profile = self._api_request(fetch, f"/user/{user_id}", params={"full": 1})
        if not profile:
            return

        username = profile.get("name", user_id)
        collection_name = f"{user_id}_{username}"

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

        all_works = self._api_request(fetch, f"/user/{user_id}/profile/all") or {}
        work_ids = list(all_works.get("illusts", {}).keys()) + list(
            all_works.get("manga", {}).keys()
        )

        for work_id in work_ids:
            yield from self._extract_artwork(fetch, work_id, collection_name)
