import logging
import os
import re

from collections.abc import Generator
from pathlib import Path
from typing import Any

import requests

from megaloader.plugin import BasePlugin, Item


logger = logging.getLogger(__name__)


class Pixiv(BasePlugin):
    BASE_URL = "https://www.pixiv.net"

    def __init__(self, url: str, **kwargs: Any) -> None:
        super().__init__(url, **kwargs)
        self.session = self._create_pixiv_session()
        self.content_id, self.is_artwork = self._parse_url()

    def _create_pixiv_session(self) -> requests.Session:
        session = self._create_session()
        session.headers.update({"Referer": f"{self.BASE_URL}/"})
        if sess_id := os.getenv("PIXIV_PHPSESSID"):
            session.cookies.set("PHPSESSID", sess_id, domain=".pixiv.net")
        return session

    def _parse_url(self) -> tuple[str, bool]:
        if match := re.search(r"artworks/(\d+)", self.url):
            return match.group(1), True
        if match := re.search(r"users/(\d+)|member\.php\?id=(\d+)", self.url):
            return match.group(1) or match.group(2), False
        raise ValueError("Invalid Pixiv URL")

    def _api_request(self, endpoint: str, params: dict | None = None) -> Any:
        try:
            resp = self.session.get(
                f"{self.BASE_URL}/ajax{endpoint}", params=params, timeout=30
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("body") if not data.get("error") else None
        except Exception:
            logger.exception("Pixiv API Error: %s", endpoint)
            return None

    def extract(self) -> Generator[Item, None, None]:
        if self.is_artwork:
            yield from self._export_artwork(self.content_id)
        else:
            yield from self._export_user(self.content_id)

    def _export_artwork(
        self, artwork_id: str, album_title: str | None = None
    ) -> Generator[Item, None, None]:
        pages = self._api_request(f"/illust/{artwork_id}/pages")
        if not pages:
            # Fallback for single image
            info = self._api_request(f"/illust/{artwork_id}")
            if info and (url := info.get("urls", {}).get("original")):
                pages = [{"urls": {"original": url}}]
            else:
                return

        if not album_title:
            info = self._api_request(f"/illust/{artwork_id}")
            title = info.get("userName", "unknown") if info else "artwork"
            album_title = f"{title}_{artwork_id}"

        for i, page in enumerate(pages):
            url = page.get("urls", {}).get("original")
            if not url:
                continue

            ext = Path(url).suffix
            filename = f"{artwork_id}_p{i}{ext}"
            yield Item(
                url=url,
                filename=filename,
                album=album_title,
                meta={"referer": f"{self.BASE_URL}/artworks/{artwork_id}"},
            )

    def _export_user(self, user_id: str) -> Generator[Item, None, None]:
        profile = self._api_request(f"/user/{user_id}", params={"full": 1})
        if not profile:
            return

        user_name = profile.get("name", user_id)
        album_title = f"{user_id}_{user_name}"

        # Profile assets
        if img := profile.get("imageBig"):
            yield Item(url=img, filename=f"avatar{Path(img).suffix}", album=album_title)
        if img := (profile.get("background") or {}).get("url"):
            yield Item(url=img, filename=f"cover{Path(img).suffix}", album=album_title)

        # Works
        all_works = self._api_request(f"/user/{user_id}/profile/all") or {}
        work_ids = list(all_works.get("illusts", {}).keys()) + list(
            all_works.get("manga", {}).keys()
        )

        for work_id in work_ids:
            yield from self._export_artwork(work_id, album_title)
