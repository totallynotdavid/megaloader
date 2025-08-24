import logging
import os
import xml.etree.ElementTree as ET

from collections.abc import Generator
from typing import Any
from urllib.parse import parse_qs, unquote, urljoin, urlparse

import requests

from bs4 import BeautifulSoup

from megaloader.http import download_file as http_download
from megaloader.plugin import BasePlugin, Item


logger = logging.getLogger(__name__)


class Rule34(BasePlugin):
    """
    Plugin for rule34.xxx. Supports two modes:
    1. API Mode (recommended): Uses the official API if RULE34_API_KEY and
       RULE34_USER_ID environment variables are set. This is fast and reliable.
    2. Scraper Mode: If API keys are not found, it falls back to scraping
       the website. This is slower and more fragile but requires no setup.

    Supports two types of URLs:
    - Single post by ID: https://rule34.xxx/index.php?page=post&s=view&id={postId}
    - Gallery by tags:   https://rule34.xxx/index.php?page=post&s=list&tags={tags}
    """

    API_BASE_URL = "https://api.rule34.xxx/index.php"
    WEB_BASE_URL = "https://rule34.xxx/index.php"

    def __init__(self, url: str, **kwargs: Any) -> None:
        super().__init__(url, **kwargs)
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)

        # we prioritize ID over Tags
        self.post_id = query_params.get("id", [None])[0]
        self.tags = []
        if not self.post_id:
            tags_str = query_params.get("tags", [""])[0]
            self.tags = tags_str.replace("+", " ").strip().split()

        if not self.post_id and not self.tags:
            raise ValueError(
                "URL must contain either an 'id' or 'tags' query parameter."
            )

        self.session = requests.Session()
        self.session.headers["User-Agent"] = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )

        self.api_key = os.getenv("RULE34_API_KEY")
        self.user_id = os.getenv("RULE34_USER_ID")
        self.use_api = bool(self.api_key and self.user_id)

        logger.debug(
            f"Initialized Rule34 plugin with "
            f"{'post_id=' + self.post_id if self.post_id else 'tags=' + str(self.tags)}"
        )

    def export(self) -> Generator[Item, None, None]:
        if self.post_id:
            yield from self._export_single()
        elif self.use_api:
            yield from self._export_api()
        else:
            yield from self._export_scraper()

    def _export_single(self) -> Generator[Item, None, None]:
        """Download a single post by ID."""
        post_url = f"{self.WEB_BASE_URL}?page=post&s=view&id={self.post_id}"
        try:
            res = self.session.get(post_url, timeout=30)
            res.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Failed to fetch post {self.post_id}: {e}")
            return

        soup = BeautifulSoup(res.text, "html.parser")
        file_url = None

        # First: we try to find the "Original image" link first, as it's usually the best quality
        original_link = soup.find(
            "a", string=lambda t: t and "Original image" in t.strip()
        )
        if original_link and original_link.get("href"):
            file_url = original_link["href"]

        # Second: If not found, check for a video source. This handles video posts.
        if not file_url:
            video_source = soup.select_one("video > source")
            if video_source and video_source.get("src"):
                file_url = video_source.get("src")

        # Third: as a fallback for standard image posts, check for the main image tag.
        if not file_url:
            img_tag = soup.select_one("img#image")
            if img_tag and img_tag.get("src"):
                file_url = img_tag.get("src")

        if not file_url:
            logger.warning(f"Could not find download link on post {self.post_id}")
            return

        if file_url.startswith("//"):
            file_url = "https:" + file_url

        filename = os.path.basename(unquote(urlparse(file_url).path))
        yield Item(url=file_url, filename=filename, album_title=f"post_{self.post_id}")

    def _export_api(self) -> Generator[Item, None, None]:
        """Fetch posts from the Rule34 API by tags."""
        logger.info(f"Starting API export for tags: {' '.join(self.tags)}")
        page_id = 0
        limit = 1000
        album_title = "_".join(sorted(self.tags))

        while True:
            params = {
                "page": "dapi",
                "s": "post",
                "q": "index",
                "tags": " ".join(self.tags),
                "pid": page_id,
                "limit": limit,
                "api_key": self.api_key,
                "user_id": self.user_id,
            }
            try:
                response = self.session.get(
                    self.API_BASE_URL, params=params, timeout=30
                )
                response.raise_for_status()
                root = ET.fromstring(response.content)
            except (requests.RequestException, ET.ParseError) as e:
                logger.error(f"Failed to fetch or parse API page {page_id}: {e}")
                break

            posts = list(root.iter("post"))
            if not posts:
                break

            for post in posts:
                file_url = post.get("file_url")
                if not file_url:
                    continue
                if file_url.startswith("//"):
                    file_url = "https:" + file_url
                filename = os.path.basename(unquote(urlparse(file_url).path))
                yield Item(
                    url=file_url,
                    filename=filename,
                    album_title=album_title,
                    file_id=post.get("id"),
                    metadata={"tags": post.get("tags")},
                )
            page_id += 1

    def _export_scraper(self) -> Generator[Item, None, None]:
        """Scrape gallery by tags."""
        logger.info(f"Starting scraper export for tags: {' '.join(self.tags)}")
        pid = 0
        posts_per_page = 42
        album_title = "_".join(sorted(self.tags))
        seen_urls = set()

        while True:
            params = {
                "page": "post",
                "s": "list",
                "tags": " ".join(self.tags),
                "pid": pid,
            }
            try:
                res = self.session.get(self.WEB_BASE_URL, params=params, timeout=30)
                res.raise_for_status()
            except requests.RequestException as e:
                logger.error(f"Failed to fetch gallery page with pid {pid}: {e}")
                break

            soup = BeautifulSoup(res.text, "html.parser")
            post_links = soup.select("div.image-list span.thumb > a")

            if not post_links:
                break

            for link in post_links:
                post_url = urljoin(self.WEB_BASE_URL, str(link.get("href")))
                if post_url in seen_urls:
                    continue
                seen_urls.add(post_url)

                try:
                    post_res = self.session.get(post_url, timeout=30)
                    post_res.raise_for_status()
                    post_soup = BeautifulSoup(post_res.text, "html.parser")

                    original_link = post_soup.find("a", string="Original image")
                    if original_link and original_link.get("href"):
                        file_url = original_link["href"]
                    else:
                        img_tag = post_soup.select_one("img#image")
                        if not img_tag:
                            continue
                        file_url = img_tag.get("src")

                    if file_url.startswith("//"):
                        file_url = "https:" + file_url
                    filename = os.path.basename(unquote(urlparse(file_url).path))
                    yield Item(url=file_url, filename=filename, album_title=album_title)
                except requests.RequestException as e:
                    logger.warning(f"Failed to process post page {post_url}: {e}")

            pid += posts_per_page

    def download_file(self, item: Item, output_dir: str) -> bool:
        result = http_download(item.url, output_dir, item.filename)
        return result is not None
