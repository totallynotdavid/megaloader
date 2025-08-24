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

    Accepts URLs with tags, e.g.,
    https://rule34.xxx/index.php?page=post&s=list&tags=some_tag
    """

    API_BASE_URL = "https://api.rule34.xxx/index.php"
    WEB_BASE_URL = "https://rule34.xxx/index.php"

    def __init__(self, url: str, **kwargs: Any) -> None:
        super().__init__(url, **kwargs)
        self.tags = self._get_tags_from_url(url)
        if not self.tags:
            raise ValueError(
                "No tags found in URL. URL must contain a 'tags' query parameter."
            )

        self.session = requests.Session()
        self.session.headers["User-Agent"] = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )

        # Check for API credentials and decide which mode to use
        self.api_key = os.getenv("RULE34_API_KEY")
        self.user_id = os.getenv("RULE34_USER_ID")
        self.use_api = bool(self.api_key and self.user_id)

        if self.use_api:
            logger.info("RULE34_API_KEY and RULE34_USER_ID found. Using API mode.")
        else:
            logger.info(
                "RULE34 API credentials not found. Falling back to scraper mode."
            )
        logger.debug(f"Initialized Rule34 plugin with tags: {self.tags}")

    def _get_tags_from_url(self, url: str) -> list[str]:
        """Extracts search tags from the URL query string."""
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        tags_str = query_params.get("tags", [""])[0]
        return tags_str.replace("+", " ").strip().split()

    def export(self) -> Generator[Item, None, None]:
        """Dispatches to the appropriate export method based on configuration."""
        if self.use_api:
            yield from self._export_api()
        else:
            yield from self._export_scraper()

    def _export_api(self) -> Generator[Item, None, None]:
        """Fetches posts from the Rule34 API and yields them as Items."""
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
                logger.info(f"No more posts found on API page {page_id}.")
                break

            logger.info(f"Found {len(posts)} posts on API page {page_id}.")
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
        """Scrapes the Rule34 website to find post URLs and yields them as Items."""
        logger.info(f"Starting scraper export for tags: {' '.join(self.tags)}")
        pid = 0  # The website uses 'pid' as a post offset, not a page number
        posts_per_page = 42  # Standard number of posts on a gallery page
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
                list_page_res = self.session.get(
                    self.WEB_BASE_URL, params=params, timeout=30
                )
                list_page_res.raise_for_status()
            except requests.RequestException as e:
                logger.error(f"Failed to fetch gallery page with pid {pid}: {e}")
                break

            soup = BeautifulSoup(list_page_res.text, "html.parser")
            post_links = soup.select("div.image-list span.thumb > a")

            if not post_links:
                logger.info(f"No more posts found on page with pid {pid}.")
                break

            logger.info(f"Found {len(post_links)} post links on page with pid {pid}.")
            for link in post_links:
                post_url = urljoin(self.WEB_BASE_URL, str(link.get("href")))
                if post_url in seen_urls:
                    continue
                seen_urls.add(post_url)

                try:
                    post_page_res = self.session.get(post_url, timeout=30)
                    post_page_res.raise_for_status()
                    post_soup = BeautifulSoup(post_page_res.text, "html.parser")

                    # Find the "Original image" link, which is the most reliable
                    # source for the full-resolution file URL.
                    original_link = post_soup.find("a", string="Original image")
                    if original_link and original_link.get("href"):
                        file_url = original_link["href"]
                    else:
                        # Fallback for images (not videos)
                        img_tag = post_soup.select_one("img#image")
                        if img_tag:
                            file_url = img_tag.get("src")
                        else:
                            logger.warning(
                                f"Could not find download link on {post_url}"
                            )
                            continue

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
