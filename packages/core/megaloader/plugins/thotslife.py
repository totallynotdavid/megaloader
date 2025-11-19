import logging
from collections.abc import Generator
from pathlib import Path
from urllib.parse import unquote, urlparse

from bs4 import BeautifulSoup

from megaloader.item import DownloadItem
from megaloader.plugin import BasePlugin

logger = logging.getLogger(__name__)


class Thotslife(BasePlugin):
    """Extract media from Thotslife posts."""

    def extract(self) -> Generator[DownloadItem, None, None]:
        response = self.session.get(self.url, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        
        # Get post title
        title_tag = soup.find("h1", class_="entry-title")
        collection_name = title_tag.text.strip() if title_tag else "thotslife_post"

        body = soup.find("div", itemprop="articleBody")
        if not body:
            return

        seen = set()

        # Extract videos
        for source in body.select("video > source[src]"):
            if src := source.get("src"):
                src_str = str(src)
                if src_str not in seen:
                    seen.add(src_str)
                    filename = (
                        Path(unquote(urlparse(src_str).path)).name
                        or f"{collection_name}.mp4"
                    )
                    
                    yield DownloadItem(
                        download_url=src_str,
                        filename=filename,
                        collection_name=collection_name,
                    )

        # Extract images
        for img in body.select("img[data-src]"):
            if src := img.get("data-src"):
                src_str = str(src)
                
                # Skip base64 embedded images
                if not src_str.startswith("data:") and src_str not in seen:
                    seen.add(src_str)
                    filename = Path(unquote(urlparse(src_str).path)).name or "image.jpg"
                    
                    yield DownloadItem(
                        download_url=src_str,
                        filename=filename,
                        collection_name=collection_name,
                    )
