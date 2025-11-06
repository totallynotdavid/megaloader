import base64
import html
import logging
import math
import re

from collections.abc import Generator
from pathlib import Path
from typing import Any
from urllib.parse import quote, urljoin, urlparse

import requests

from megaloader.plugin import BasePlugin, Item


logger = logging.getLogger(__name__)


class Bunkr(BasePlugin):
    API_URL = "https://apidl.bunkr.ru/api/_001_v2"

    def __init__(self, url: str, **kwargs: Any) -> None:
        super().__init__(url, **kwargs)
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            },
        )

    def export(self) -> Generator[Item, None, None]:
        """Extract files from Bunkr URL (album or single file)."""
        logger.info("Processing Bunkr URL: %s", self.url)

        response = self.session.get(self.url, allow_redirects=True, timeout=30)
        response.raise_for_status()

        resolved_url = response.url
        content = response.text

        if "/a/" in resolved_url:
            # Album page - extract file links
            yield from self._process_album(content, resolved_url)
        elif "/f/" in resolved_url:
            # Single file viewer page
            yield from self._process_file_page(content, resolved_url)
        else:
            logger.warning("Unrecognized Bunkr URL format: %s", resolved_url)

    def _process_album(
        self,
        content: str,
        base_url: str,
    ) -> Generator[Item, None, None]:
        """Extract file links from album page."""
        # Find file links using regex
        file_links = re.findall(r'href="(/f/[^"]+)"', content)

        if not file_links:
            logger.warning("No files found in album")
            return

        logger.info("Found %d files in album", len(file_links))

        seen_urls = set()
        for link in file_links:
            # Skip JavaScript templates
            if "file.slug" in link or "+" in link:
                continue
            file_url = urljoin(base_url, link)
            if file_url in seen_urls:
                continue
            seen_urls.add(file_url)

            yield from self._process_file_url(file_url)

    def _process_file_page(
        self,
        content: str,
        file_url: str,
    ) -> Generator[Item, None, None]:
        """Process single file viewer page."""
        yield from self._process_file_url(file_url)

    def _process_file_url(self, file_url: str) -> Generator[Item, None, None]:
        """Process a single file URL to get download page."""
        response = self.session.get(file_url, timeout=30)
        response.raise_for_status()

        # Find download button
        download_match = re.search(
            r'<a[^>]+class="[^"]*btn-main[^"]*"[^>]+href="([^"]+)"[^>]*>Download</a>',
            response.text,
        )
        if not download_match:
            logger.warning("No download button found for %s", file_url)
            return

        download_url = urljoin(file_url, download_match.group(1))

        # Extract filename from og:title or script
        filename = self._extract_filename(response.text)
        if not filename:
            filename = f"bunkr_file_{Path(urlparse(file_url).path).name}"

        # Extract file ID from URL
        file_id = Path(urlparse(file_url).path).name

        yield Item(url=download_url, filename=filename, file_id=file_id)

    def _extract_filename(self, content: str) -> str | None:
        """Extract original filename from page content."""
        # Try og:title first
        og_match = re.search(r'<meta property="og:title" content="([^"]+)"', content)
        if og_match:
            return html.unescape(og_match.group(1)).strip()

        # Try script variable
        script_match = re.search(r'var ogname\s*=\s*"([^"]+)"', content)
        if script_match:
            return html.unescape(script_match.group(1)).strip()

        return None

    def download_file(self, item: Item, output_dir: str) -> bool:
        """Download file using Bunkr's encrypted API."""
        try:
            # Get file ID from download page
            response = self.session.get(item.url, timeout=30)
            response.raise_for_status()

            file_id = self._extract_file_id(response.text, item.url)
            if not file_id:
                logger.error("Could not extract file ID from %s", item.url)
                return False

            # Call API to get encrypted URL
            api_response = self.session.post(
                self.API_URL,
                json={"id": file_id},
                timeout=30,
            )
            api_response.raise_for_status()
            api_data = api_response.json()

            # Decrypt the download URL
            download_url = self._decrypt_url(api_data, item.filename)
            if not download_url:
                logger.error("Failed to decrypt download URL")
                return False

            # Download the file
            return self._download_file_direct(
                download_url,
                item.filename,
                output_dir,
                item.url,
            )

        except Exception:
            logger.exception("Failed to download %s", item.filename)
            return False

    def _extract_file_id(self, content: str, url: str) -> str | None:
        """Extract file ID from download page."""
        # Try data-id attribute first
        id_match = re.search(r'data-id="([^"]+)"', content)
        if id_match:
            return id_match.group(1)

        # Fall back to URL parsing
        url_match = re.search(r"/file/([^/?#]+)", url)
        if url_match:
            return url_match.group(1)

        return None

    def _decrypt_url(self, api_data: dict[str, Any], filename: str) -> str | None:
        """Decrypt the download URL from API response."""
        try:
            timestamp = api_data["timestamp"]
            encrypted_b64 = api_data["url"]

            # Generate decryption key
            key_str = f"SECRET_KEY_{math.floor(timestamp / 3600)}"
            key_bytes = key_str.encode("utf-8")

            # Decrypt URL
            encrypted_bytes = base64.b64decode(encrypted_b64)
            decrypted = bytearray(len(encrypted_bytes))

            for i in range(len(encrypted_bytes)):
                decrypted[i] = encrypted_bytes[i] ^ key_bytes[i % len(key_bytes)]

            base_url = decrypted.decode("utf-8")
            return f"{base_url}?n={quote(filename)}"

        except (KeyError, ValueError, Exception):
            logger.exception("URL decryption failed")
            return None

    def _download_file_direct(
        self,
        url: str,
        filename: str,
        output_dir: str,
        referer: str,
    ) -> bool:
        """Download file with proper headers."""
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        output_path = Path(output_dir) / filename

        if output_path.exists():
            logger.info("File already exists: %s", filename)
            return True

        headers = {
            "Referer": f"{urlparse(referer).scheme}://{urlparse(referer).netloc}/",
        }

        try:
            with self.session.get(
                url,
                headers=headers,
                stream=True,
                timeout=60,
            ) as response:
                response.raise_for_status()
                with output_path.open("wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)

        except Exception:
            logger.exception("Download failed")
            if output_path.exists():
                output_path.unlink()
            return False
        else:
            logger.info("Downloaded: %s", filename)
            return True
