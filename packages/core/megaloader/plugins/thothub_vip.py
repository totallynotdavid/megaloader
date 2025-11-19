import json
import logging

from collections.abc import Generator
from pathlib import Path
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from megaloader.plugin import BasePlugin, Item


logger = logging.getLogger(__name__)


class ThothubVIP(BasePlugin):
    def extract(self) -> Generator[Item, None, None]:
        if "/video/" in self.url:
            yield from self._export_video()
        elif "/album/" in self.url:
            yield from self._export_album()
        else:
            logger.warning("Unsupported ThothubVIP URL")

    def _export_video(self) -> Generator[Item, None, None]:
        resp = self.session.get(self.url, timeout=30)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        script = soup.find("script", type="application/ld+json")
        if not script:
            return

        try:
            meta = json.loads(script.get_text().strip())
            if url := meta.get("contentUrl"):
                name = meta.get("name", "video")
                yield Item(url=urljoin(self.url, url), filename=f"{name}.mp4")
        except Exception:
            logger.exception("JSON-LD parse error")

    def _export_album(self) -> Generator[Item, None, None]:
        resp = self.session.get(self.url, timeout=30)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        h1_tag = soup.find("h1", class_="title")
        title = h1_tag.text.strip() if h1_tag else "album"

        for link in soup.select("div.album-inner a.item.album-img[href]"):
            href = link.get("href")
            if href:
                full_url = urljoin(self.url, str(href))
                fname = Path(urlparse(full_url).path.strip("/")).name
                if fname:
                    yield Item(url=full_url, filename=fname, album=title)
