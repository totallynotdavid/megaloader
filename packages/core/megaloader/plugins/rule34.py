import logging
import xml.etree.ElementTree as ET

from collections.abc import Generator
from typing import Any
from urllib.parse import parse_qs, urljoin, urlparse

from bs4 import BeautifulSoup

from megaloader.fetcher import Fetcher, Request
from megaloader.filenames import filename_from_url
from megaloader.item import DownloadItem
from megaloader.pagination import crawl_pages
from megaloader.parsing import parse_html, unique
from megaloader.plugin import BasePlugin


logger = logging.getLogger(__name__)

SITE_BASE = "https://rule34.xxx"
API_BASE = "https://api.rule34.xxx"
POSTS_PER_PAGE = 42


def parse_query(url: str) -> tuple[str | None, list[str]]:
    """Return (post_id, tags) from a Rule34 listing or post URL query string."""
    query = parse_qs(urlparse(url).query)
    post_id = query.get("id", [None])[0]
    tags = query.get("tags", [""])[0].split()
    return post_id, tags


def parse_media_url(soup: BeautifulSoup) -> str | None:
    """Find the original media URL on a post page (image link, video, or img tag)."""
    for link in soup.find_all("a"):
        if "Original image" in str(link.string) and (href := link.get("href")):
            return str(href)

    if (video := soup.select_one("video > source")) and (src := video.get("src")):
        return str(src)

    if (img := soup.select_one("img#image")) and (src := img.get("src")):
        return str(src)

    return None


def parse_listing_hrefs(soup: BeautifulSoup) -> list[str]:
    """Return thumbnail post hrefs from a scraped listing page."""
    return [
        str(href)
        for link in soup.select("div.image-list span.thumb > a")
        if (href := link.get("href"))
    ]


def parse_api_posts(xml: bytes) -> list[ET.Element] | None:
    """Parse the API XML into <post> elements, or None when the body is not XML."""
    try:
        root = ET.fromstring(xml)
    except ET.ParseError:
        return None
    return list(root.iter("post"))


def build_item(
    url: str, collection_name: str, post_id: str | None = None
) -> DownloadItem:
    url = f"https:{url}" if url.startswith("//") else url

    return DownloadItem(
        download_url=url,
        filename=filename_from_url(url),
        collection_name=collection_name,
        source_id=post_id,
    )


class Rule34(BasePlugin):
    """Extract posts from Rule34."""

    def __init__(self, url: str, **options: Any) -> None:
        super().__init__(url, **options)
        self.post_id, self.tags = parse_query(url)

        if not self.post_id and not self.tags:
            msg = "URL must contain 'id' or 'tags' parameter"
            raise ValueError(msg)

        self.api_key = self.option("api_key", env="RULE34_API_KEY")
        self.user_id = self.option("user_id", env="RULE34_USER_ID")

    def extract(self, fetch: Fetcher) -> Generator[DownloadItem, None, None]:
        if self.post_id:
            yield from self._extract_single_post(fetch)
        elif self.api_key and self.user_id:
            logger.debug("Using API extraction")
            yield from self._extract_via_api(fetch)
        else:
            logger.debug(
                "Using web scraping (slower, set API credentials for better performance)"
            )
            yield from self._extract_via_scraper(fetch)

    def _extract_single_post(
        self, fetch: Fetcher
    ) -> Generator[DownloadItem, None, None]:
        url = f"{SITE_BASE}/index.php?page=post&s=view&id={self.post_id}"
        response = fetch(Request(url))

        if media_url := parse_media_url(parse_html(response.text)):
            yield build_item(media_url, f"post_{self.post_id}", self.post_id)

    def _extract_via_api(self, fetch: Fetcher) -> Generator[DownloadItem, None, None]:
        """Extract using official API (faster, more reliable)."""
        collection_name = self._collection_name()

        for response in crawl_pages(fetch, self._api_request, start=0):
            posts = parse_api_posts(response.content)

            if not posts:
                break

            for post in posts:
                if url := post.get("file_url"):
                    yield build_item(url, collection_name, post.get("id"))

    def _extract_via_scraper(
        self, fetch: Fetcher
    ) -> Generator[DownloadItem, None, None]:
        """Extract by scraping web pages (fallback method)."""
        collection_name = self._collection_name()

        for post_url in unique(self._listing_post_urls(fetch)):
            post_response = fetch(Request(post_url))

            if media_url := parse_media_url(parse_html(post_response.text)):
                yield build_item(media_url, collection_name)

    def _listing_post_urls(self, fetch: Fetcher) -> Generator[str, None, None]:
        for response in crawl_pages(
            fetch, self._listing_request, start=0, step=POSTS_PER_PAGE
        ):
            hrefs = parse_listing_hrefs(parse_html(response.text))

            if not hrefs:
                return

            for href in hrefs:
                yield urljoin(f"{SITE_BASE}/", href)

    def _collection_name(self) -> str:
        return "_".join(sorted(self.tags))

    def _api_request(self, page: int) -> Request:
        return Request(
            f"{API_BASE}/index.php",
            params={
                "page": "dapi",
                "s": "post",
                "q": "index",
                "tags": " ".join(self.tags),
                "pid": page,
                "limit": 1000,
                "api_key": self.api_key,
                "user_id": self.user_id,
            },
        )

    def _listing_request(self, pid: int) -> Request:
        """Build a listing request; Rule34 pages by post offset, 42 per page."""
        return Request(
            f"{SITE_BASE}/index.php",
            params={
                "page": "post",
                "s": "list",
                "tags": " ".join(self.tags),
                "pid": pid,
            },
        )
