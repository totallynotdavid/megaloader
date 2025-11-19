import logging

from collections.abc import Generator
from pathlib import Path
from urllib.parse import unquote, urlparse

from bs4 import BeautifulSoup

from megaloader.plugin import BasePlugin, Item


logger = logging.getLogger(__name__)


class Thotslife(BasePlugin):
    def extract(self) -> Generator[Item, None, None]:
        resp = self.session.get(self.url, timeout=30)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        title_tag = soup.find("h1", class_="entry-title")
        album_title = title_tag.text.strip() if title_tag else "thotslife_album"

        body = soup.find("div", itemprop="articleBody")
        if not body:
            return

        seen = set()

        # Videos
        for src in [s.get("src") for s in body.select("video > source[src]")]:
            if src and src not in seen:
                seen.add(src)
                src_str = str(src)
                fname = (
                    Path(unquote(urlparse(src_str).path)).name or f"{album_title}.mp4"
                )
                yield Item(url=src_str, filename=fname, album=album_title)

        # Images
        for src in [i.get("data-src") for i in body.select("img[data-src]")]:
            if src and src not in seen:
                src_str = str(src)
                if not src_str.startswith("data:"):
                    seen.add(src)
                    fname = Path(unquote(urlparse(src_str).path)).name or "image.jpg"
                    yield Item(url=src_str, filename=fname, album=album_title)
