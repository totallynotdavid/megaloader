import contextlib
import logging
import os
import re

from collections.abc import Generator
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests

from megaloader.plugin import BasePlugin, Item


logger = logging.getLogger(__name__)


class Pixiv(BasePlugin):
    """
    Plugin for downloading images from Pixiv.
    Supports user profiles and single artwork pages.
    - https://www.pixiv.net/en/users/{userId}
    - https://www.pixiv.net/en/artworks/{artworkId}
    - http://www.pixiv.net/member.php?id={userId}.

    To download R-18 or private content, set the PIXIV_PHPSESSID environment
    variable to your 'PHPSESSID' cookie value from pixiv.net.
    """

    BASE_URL = "https://www.pixiv.net"
    AJAX_URL = f"{BASE_URL}/ajax"
    PROFILE_SUBFOLDER = "profile"

    _ARTWORK_RE = re.compile(r"pixiv\.net/(?:en/)?artworks/(\d+)")
    _USER_RE = re.compile(r"pixiv\.net/(?:en/)?users/(\d+)")
    _USER_OLD_RE = re.compile(r"pixiv\.net/member\.php\?id=(\d+)")

    def __init__(self, url: str, **kwargs: Any) -> None:
        super().__init__(url, **kwargs)
        self.session = self._create_session()
        self.url_type: str | None = None
        self.content_id: str | None = None
        self._parse_url()

    def _create_session(self) -> requests.Session:
        session = requests.Session()
        session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Referer": f"{self.BASE_URL}/",
            },
        )

        if pixiv_session_id := os.getenv("PIXIV_PHPSESSID"):
            session.cookies.set("PHPSESSID", pixiv_session_id, domain=".pixiv.net")
            logger.info("Loaded PHPSESSID from environment variable")
        else:
            logger.warning(
                "PIXIV_PHPSESSID not set. Access will be limited to public posts only (some public posts may still be restricted by Pixiv).",
            )
        return session

    def _parse_url(self) -> None:
        if match := self._ARTWORK_RE.search(self.url):
            self.url_type = "artwork"
            self.content_id = match.group(1)
        elif (match := self._USER_RE.search(self.url)) or (
            match := self._USER_OLD_RE.search(self.url)
        ):
            self.url_type = "user"
            self.content_id = match.group(1)
        else:
            msg = f"Invalid or unsupported Pixiv URL: {self.url}"
            raise ValueError(msg)
        logger.debug("Parsed URL type: %s, ID: %s", self.url_type, self.content_id)

    def _api_request(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
    ) -> Any | None:
        """
        Return the 'body' from Pixiv's ajax response.
        The body may be a dict or a list depending on endpoint.
        """
        url = f"{self.AJAX_URL}{endpoint}"
        request_params = {"lang": "en"}
        if params:
            request_params.update(params)

        try:
            response = self.session.get(url, params=request_params, timeout=30)
            response.raise_for_status()
            data = response.json()
            if isinstance(data, dict) and data.get("error"):
                logger.error("Pixiv API error for %s: %s", url, data.get("message"))
                return None
            return data.get("body") if isinstance(data, dict) else None
        except requests.RequestException:
            logger.exception("API request failed for %s", url)
        except ValueError:
            logger.exception("Failed to decode JSON from API response for %s", url)
        return None

    def _sanitize_name(self, name: str) -> str:
        return re.sub(r'[<>:"/\\|?*]', "_", name).strip()[:200]

    def _get_extension_from_url(self, url: str) -> str:
        path = urlparse(url).path
        return Path(path).suffix or ".jpg"

    def export(self) -> Generator[Item, None, None]:
        if not self.url_type or not self.content_id:
            logger.error("URL was not parsed correctly.")
            return

        if self.url_type == "artwork":
            yield from self._export_artwork_pages(self.content_id)
        elif self.url_type == "user":
            yield from self._export_user(self.content_id)

    def _export_user(self, user_id: str) -> Generator[Item, None, None]:
        logger.info("Fetching profile for user ID: %s", user_id)
        profile_data = self._api_request(f"/user/{user_id}", params={"full": 1})
        if not profile_data:
            logger.error("Could not retrieve profile for user %s", user_id)
            return

        if not isinstance(profile_data, dict):
            logger.error(
                "Unexpected profile data shape for user %s: %s",
                user_id,
                type(profile_data).__name__,
            )
            return

        user_name = profile_data.get("name", f"user_{user_id}")
        album_title = f"{user_id}_{self._sanitize_name(user_name)}"
        logger.info("Album will be saved to: %s", album_title)

        yield from self._export_user_profile_assets(profile_data, album_title)

        logger.info("Fetching artwork list for user: %s", user_name)
        all_works_data = self._api_request(f"/user/{user_id}/profile/all")
        if not all_works_data:
            logger.warning("Could not retrieve artwork list for user %s", user_id)
            return

        if not isinstance(all_works_data, dict):
            logger.warning(
                "Unexpected artwork list shape for user %s: %s",
                user_id,
                type(all_works_data).__name__,
            )
            return

        illust_ids, manga_ids = [], []
        illusts_data = all_works_data.get("illusts", {})
        if isinstance(illusts_data, dict):
            illust_ids = list(illusts_data.keys())
            logger.debug("Found %d illustration works.", len(illust_ids))

        manga_data = all_works_data.get("manga", [])
        if isinstance(manga_data, dict):
            manga_ids = list(manga_data.keys())
            logger.debug("Found %d manga works.", len(manga_ids))

        artwork_ids = illust_ids + manga_ids

        if not artwork_ids:
            logger.info("No public artworks found for user %s", user_id)
            return

        logger.info("Found %d artworks. Fetching details...", len(artwork_ids))
        for i, artwork_id in enumerate(artwork_ids, 1):
            logger.debug(
                "Processing artwork %d/%d: %s",
                i,
                len(artwork_ids),
                artwork_id,
            )
            yield from self._export_artwork_pages(artwork_id, album_title)

    def _export_user_profile_assets(
        self,
        profile_data: dict[str, Any],
        album_title: str,
    ) -> Generator[Item, None, None]:
        logger.debug("Processing profile assets (avatar and cover image).")
        user_id = profile_data.get("userId")
        referer = f"{self.BASE_URL}/users/{user_id}" if user_id else self.BASE_URL

        if avatar_url := profile_data.get("imageBig"):
            ext = self._get_extension_from_url(avatar_url)
            filename = str(Path(self.PROFILE_SUBFOLDER) / f"avatar{ext}")
            yield Item(
                url=avatar_url,
                filename=filename,
                album_title=album_title,
                metadata={"referer": referer},
            )

        if cover_url := (profile_data.get("background") or {}).get("url"):
            ext = self._get_extension_from_url(cover_url)
            filename = str(Path(self.PROFILE_SUBFOLDER) / f"cover{ext}")
            yield Item(
                url=cover_url,
                filename=filename,
                album_title=album_title,
                metadata={"referer": referer},
            )

    def _export_artwork_pages(
        self,
        artwork_id: str,
        album_title: str | None = None,
    ) -> Generator[Item, None, None]:
        page_data = self._api_request(f"/illust/{artwork_id}/pages")
        if not page_data:
            # Fallback for single images or pages that don't use the /pages endpoint
            illust_data = self._api_request(f"/illust/{artwork_id}")
            if isinstance(illust_data, dict) and (
                url := illust_data.get("urls", {}).get("original")
            ):
                page_data = [{"urls": {"original": url}}]
            else:
                logger.warning("Failed to get any image URL for artwork %s", artwork_id)
                return

        if isinstance(page_data, dict):
            page_data = [page_data]
        elif not isinstance(page_data, list):
            logger.warning(
                "Unexpected page data type for artwork %s: %s",
                artwork_id,
                type(page_data).__name__,
            )
            return

        if not album_title:
            album_title = self._get_album_title(artwork_id)

        has_multiple_pages = len(page_data) > 1

        for i, page in enumerate(page_data):
            if not isinstance(page, dict):
                logger.warning("page[%d] is not a dict, skipping: %r", i, page)
                continue

            page_url = page.get("urls", {}).get("original")
            if not page_url:
                logger.warning(
                    "No usable image URL for artwork %s page %d",
                    artwork_id,
                    i,
                )
                continue

            ext = self._get_extension_from_url(page_url)

            if has_multiple_pages:
                filename = str(Path(artwork_id) / f"{artwork_id}_p{i}{ext}")
            else:
                filename = f"{artwork_id}_p{i}{ext}"

            yield Item(
                url=page_url,
                filename=filename,
                album_title=album_title,
                metadata={"referer": f"{self.BASE_URL}/artworks/{artwork_id}"},
            )

    def _get_album_title(self, artwork_id: str) -> str:
        illust_info = self._api_request(f"/illust/{artwork_id}")
        if isinstance(illust_info, dict):
            artist_name = illust_info.get("userName", "unknown_artist")
            artist_id = illust_info.get("userId", "unknown")
            return f"{artist_id}_{self._sanitize_name(artist_name)}"
        return f"artwork_{artwork_id}"

    def download_file(self, item: Item, output_dir: str) -> bool:
        full_path = Path(output_dir) / item.filename
        full_path.parent.mkdir(parents=True, exist_ok=True)

        if full_path.exists():
            logger.info("File already exists: %s", item.filename)
            return True

        headers = dict(self.session.headers)
        if item.metadata and "referer" in item.metadata:
            headers["Referer"] = item.metadata["referer"]

        try:
            with self.session.get(
                item.url,
                headers=headers,
                stream=True,
                timeout=180,
            ) as response:
                response.raise_for_status()
                with full_path.open("wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
            logger.info("Downloaded: %s", item.filename)
        except requests.RequestException:
            logger.exception("Download failed for %s", item.filename)
            if full_path.exists():
                with contextlib.suppress(OSError):
                    full_path.unlink()
            return False
        else:
            return True
