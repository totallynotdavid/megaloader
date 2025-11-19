import logging
import re

from collections.abc import Generator
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urljoin, urlparse

from bs4 import BeautifulSoup

from megaloader.plugin import BasePlugin, Item


logger = logging.getLogger(__name__)


class Fapello(BasePlugin):
    def __init__(self, url: str, **kwargs: Any) -> None:
        super().__init__(url, **kwargs)
        self.session.headers.update({"Referer": "https://fapello.com/"})
        self.model = self._get_model_from_url(url)

    def _get_model_from_url(self, url: str) -> str:
        match = re.search(r"fapello\.com/([a-zA-Z0-9_\-~\.]+)", url)
        if not match or not match.group(1):
            raise ValueError("Invalid Fapello URL")
        return match.group(1).split("/")[0]

    def extract(self) -> Generator[Item, None, None]:
        logger.info("Starting export for Fapello model: %s", self.model)
        page = 1
        seen_urls = set()

        while True:
            ajax_url = f"https://fapello.com/ajax/model/{self.model}/page-{page}/"
            try:
                response = self.session.get(ajax_url, timeout=30)
                response.raise_for_status()
                if not response.text.strip():
                    break
            except Exception:
                logger.exception("Error fetching page %d", page)
                break

            soup = BeautifulSoup(response.text, "html.parser")
            thumbs = soup.select('a > div > img[src*="/content/"]')
            if not thumbs:
                break

            for img in thumbs:
                thumb_url = urljoin("https://fapello.com/", str(img["src"]))
                # Convert thumb URL to full resolution by removing suffixes like _300px
                full_url = re.sub(
                    r"_\d+px(\.(?:jpg|jpeg|png|mp4))$",
                    r"\1",
                    thumb_url,
                    flags=re.IGNORECASE,
                )

                if full_url not in seen_urls:
                    seen_urls.add(full_url)
                    filename = Path(unquote(urlparse(full_url).path)).name
                    yield Item(url=full_url, filename=filename, album=self.model)

            page += 1
