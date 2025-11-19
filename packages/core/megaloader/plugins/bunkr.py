import html
import logging
import re

from collections.abc import Generator
from pathlib import Path
from urllib.parse import urljoin, urlparse

from megaloader.plugin import BasePlugin, Item


logger = logging.getLogger(__name__)


class Bunkr(BasePlugin):
    def extract(self) -> Generator[Item, None, None]:
        logger.info("Processing Bunkr URL: %s", self.url)
        response = self.session.get(self.url, allow_redirects=True, timeout=30)
        response.raise_for_status()

        resolved_url = response.url
        content = response.text

        if "/a/" in resolved_url:
            yield from self._process_album(content, resolved_url)
        elif "/f/" in resolved_url:
            yield from self._process_file_url(resolved_url)
        else:
            logger.warning("Unrecognized Bunkr URL format: %s", resolved_url)

    def _process_album(
        self, content: str, base_url: str
    ) -> Generator[Item, None, None]:
        file_links = re.findall(r'href="(/f/[^"]+)"', content)
        if not file_links:
            logger.warning("No files found in album")
            return

        seen_urls = set()
        for link in file_links:
            if "file.slug" in link or "+" in link:
                continue
            file_url = urljoin(base_url, link)
            if file_url in seen_urls:
                continue
            seen_urls.add(file_url)
            yield from self._process_file_url(file_url)

    def _process_file_url(self, file_url: str) -> Generator[Item, None, None]:
        response = self.session.get(file_url, timeout=30)
        response.raise_for_status()

        download_match = re.search(
            r'<a[^>]+class="[^"]*btn-main[^"]*"[^>]+href="([^"]+)"[^>]*>Download</a>',
            response.text,
        )
        if not download_match:
            logger.warning("No download button found for %s", file_url)
            return

        download_url = urljoin(file_url, download_match.group(1))
        file_id = Path(urlparse(file_url).path).name

        filename = self._extract_filename(response.text)
        if not filename:
            filename = f"bunkr_file_{file_id}"

        yield Item(url=download_url, filename=filename, id=file_id)

    def _extract_filename(self, content: str) -> str | None:
        og_match = re.search(r'<meta property="og:title" content="([^"]+)"', content)
        if og_match:
            return html.unescape(og_match.group(1)).strip()
        script_match = re.search(r'var ogname\s*=\s*"([^"]+)"', content)
        if script_match:
            return html.unescape(script_match.group(1)).strip()
        return None
