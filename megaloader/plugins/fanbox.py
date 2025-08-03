import contextlib
import logging
import os
import re

from collections.abc import Generator
from typing import Any
from urllib.parse import unquote, urlparse

import requests

from megaloader.plugin import BasePlugin, Item


logger = logging.getLogger(__name__)


class Fanbox(BasePlugin):
    """
    Plugin for downloading content from a Fanbox creator's page.
    Downloads all publicly available content, and with a FANBOXSESSID,
    can also download supported paid content.
    """

    BASE_API_URL = "https://api.fanbox.cc"
    PROFILE_SUBFOLDER = "profile"

    def __init__(self, url: str, **kwargs: Any) -> None:
        super().__init__(url, **kwargs)
        self.creator_id = self._get_creator_id_from_url(url)
        self.session = self._create_session()
        self.seen_urls: set[str] = set()

    def _get_creator_id_from_url(self, url: str) -> str:
        # Covers: {creator_id}.fanbox.cc, fanbox.cc/@{creator_id}, fanbox.cc/{creator_id}
        match = re.search(
            r"//(?:www\.)?([\w-]+)\.fanbox\.cc|fanbox\.cc/(?:@)?([\w-]+)", url
        )
        if match:
            creator_id = next(group for group in match.groups() if group)
            logger.debug(f"Extracted creator ID: {creator_id}")
            return creator_id
        raise ValueError(f"Invalid Fanbox URL: Could not extract creator ID from {url}")

    def _create_session(self) -> requests.Session:
        session = requests.Session()
        session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "application/json, text/plain, */*",
                "Origin": f"https://{self.creator_id}.fanbox.cc",
                "Referer": f"https://{self.creator_id}.fanbox.cc/",
            }
        )

        if fanbox_session_id := os.getenv("FANBOX_SESSION_ID"):
            session.cookies.set("FANBOXSESSID", fanbox_session_id, domain=".fanbox.cc")
            logger.info("Loaded FANBOXSESSID from environment variable")
        else:
            logger.warning(
                "FANBOX_SESSION_ID is not set. Access will be limited to public posts only (some public posts may still be restricted by Fanbox)."
            )

        return session

    def _api_request(self, endpoint: str) -> Any:
        url = endpoint if endpoint.startswith("http") else self.BASE_API_URL + endpoint

        try:
            response = self.session.get(url, timeout=30)
            if response.status_code == 403:
                logger.warning(
                    f"Access forbidden for {url}. Content may require subscription."
                )
                return None
            if response.status_code == 404:
                logger.warning(f"Content not found: {url}")
                return None

            response.raise_for_status()
            return response.json().get("body")

        except requests.RequestException as e:
            logger.error(f"API request failed for {url}: {e}")
            return None

    def _sanitize_filename(self, filename: str) -> str:
        # Replace reserved characters and limit length
        sanitized = re.sub(r'[<>:"/\\|?*]', "_", filename).strip()
        return sanitized[:150] if sanitized else "unnamed"

    def _get_extension_from_url(self, url: str) -> str:
        path = urlparse(url).path
        return os.path.splitext(path)[1] or ".jpg"

    def _create_item(
        self, url: str, filename: str, subfolder: str = ""
    ) -> Generator[Item, None, None]:
        if url in self.seen_urls:
            return
        self.seen_urls.add(url)

        full_filename = (
            os.path.join(subfolder, self._sanitize_filename(filename))
            if subfolder
            else self._sanitize_filename(filename)
        )

        yield Item(
            url=url,
            filename=full_filename,
            album_title=self.creator_id,
        )

    def export(self) -> Generator[Item, None, None]:
        logger.info(f"Starting Fanbox export for creator: {self.creator_id}")

        yield from self._process_profile()
        yield from self._process_posts()

        logger.info("Fanbox export completed")

    def _process_profile(self) -> Generator[Item, None, None]:
        logger.info("Fetching creator profile information...")

        creator_info = self._api_request(f"/creator.get?creatorId={self.creator_id}")
        if not creator_info:
            logger.warning("Could not fetch creator profile")
            return

        assets_found = 0

        # Avatar
        if icon_url := creator_info.get("user", {}).get("iconUrl"):
            filename = f"avatar{self._get_extension_from_url(icon_url)}"
            yield from self._create_item(icon_url, filename, self.PROFILE_SUBFOLDER)
            assets_found += 1

        # Banner/cover
        if cover_url := creator_info.get("coverImageUrl"):
            filename = f"banner{self._get_extension_from_url(cover_url)}"
            yield from self._create_item(cover_url, filename, self.PROFILE_SUBFOLDER)
            assets_found += 1

        # Profile images
        for item in creator_info.get("profileItems", []):
            if isinstance(item, dict) and (image_url := item.get("imageUrl")):
                filename = os.path.basename(unquote(urlparse(image_url).path))
                if not filename:
                    filename = f"profile_image_{len(self.seen_urls)}{self._get_extension_from_url(image_url)}"
                yield from self._create_item(image_url, filename)
                assets_found += 1

        logger.info(f"Found {assets_found} profile assets")

    def _process_posts(self) -> Generator[Item, None, None]:
        page_urls = self._api_request(
            f"/post.paginateCreator?creatorId={self.creator_id}"
        )
        if not page_urls:
            logger.info("No post pages found")
            return

        post_ids: list[str] = []
        for page_url in page_urls:
            posts_summary = self._api_request(page_url)
            if posts_summary:
                post_ids.extend(str(post["id"]) for post in posts_summary)

        if not post_ids:
            logger.info("No accessible posts found")
            return

        logger.info(f"Processing {len(post_ids)} posts...")
        accessible_posts = 0

        for i, post_id in enumerate(post_ids, 1):
            logger.debug(f"Processing post {i}/{len(post_ids)} (ID: {post_id})")
            items_yielded = False
            for item in self._process_single_post(post_id):
                yield item
                items_yielded = True
            if items_yielded:
                accessible_posts += 1

        logger.info(f"Successfully processed {accessible_posts}/{len(post_ids)} posts")

    def _process_single_post(self, post_id: str) -> Generator[Item, None, None]:
        post_info = self._api_request(f"/post.info?postId={post_id}")
        if not post_info:
            return

        post_title = self._sanitize_filename(post_info.get("title", f"post_{post_id}"))
        post_subfolder = f"{post_id}_{post_title}"
        post_body = post_info.get("body", {})

        # Handle posts without body content (cover image only)
        if not post_body:
            if cover_url := post_info.get("coverImageUrl"):
                filename = f"cover{self._get_extension_from_url(cover_url)}"
                yield from self._create_item(cover_url, filename, post_subfolder)
            return

        # Process images from imageMap
        for image_id, image_data in post_body.get("imageMap", {}).items():
            if url := image_data.get("originalUrl"):
                filename = os.path.basename(unquote(urlparse(url).path))
                if not filename:
                    filename = f"image_{image_id}{self._get_extension_from_url(url)}"
                yield from self._create_item(url, filename, post_subfolder)

        # Process files from fileMap
        for file_id, file_data in post_body.get("fileMap", {}).items():
            if url := file_data.get("url"):
                name = file_data.get("name", f"file_{file_id}")
                extension = file_data.get("extension", "")
                filename = f"{name}.{extension}" if extension else name
                yield from self._create_item(url, filename, post_subfolder)

    def download_file(self, item: Item, output_dir: str) -> bool:
        full_path = os.path.join(output_dir, item.filename)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        if os.path.exists(full_path) and os.path.getsize(full_path) > 0:
            logger.debug(f"File already exists: {item.filename}")
            return True

        try:
            with self.session.get(item.url, stream=True, timeout=180) as response:
                response.raise_for_status()

                with open(full_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)

                logger.info(f"Downloaded: {item.filename}")
                return True

        except requests.RequestException as e:
            logger.error(f"Download failed for {item.filename}: {e}")
            if os.path.exists(full_path):
                with contextlib.suppress(OSError):
                    os.remove(full_path)
            return False
