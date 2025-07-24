import requests
import re
import os
import base64
import math
import logging
from urllib.parse import urljoin, urlparse, quote
from typing import Generator, Optional
from bs4 import BeautifulSoup
from ..plugin import BasePlugin
from ..utils import unentitify

logger = logging.getLogger(__name__)


class Bunkr(BasePlugin):
    API_URL = "https://apidl.bunkr.ru/api/_001_v2"

    def __init__(self, url: str, **kwargs):
        super().__init__(url)
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
        )

    def _get_base_url(self, url: str) -> str:
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"

    def _solve_encrypted_url(
        self, api_response: dict, original_filename: str
    ) -> Optional[str]:
        """
        Decrypts a base64-encoded, XOR-encrypted URL from the API response using a time-based key,
        and appends the original filename as a query parameter.

        Args:
            api_response (dict): Dictionary containing 'timestamp' and base64-encoded 'url'.
            original_filename (str): The name of the original file to include in the final URL.

        Returns:
            Optional[str]: The decrypted URL with the filename appended, or None if an error occurs.
        """
        try:
            # Extract timestamp and encrypted URL from the API response
            timestamp = api_response["timestamp"]
            encrypted_url_b64 = api_response["url"]

            # Create the decryption key using the timestamp (rounded down to the nearest hour)
            key_str = f"SECRET_KEY_{math.floor(timestamp / 3600)}"
            key_bytes = key_str.encode("utf-8")

            # Decode the base64-encoded encrypted URL
            encrypted_bytes = base64.b64decode(encrypted_url_b64)

            # Decrypt the URL using XOR with the generated key
            decrypted_bytes = bytearray(len(encrypted_bytes))
            for i in range(len(encrypted_bytes)):
                decrypted_bytes[i] = encrypted_bytes[i] ^ key_bytes[i % len(key_bytes)]

            # Convert decrypted bytes back to string to get the base URL
            base_url = decrypted_bytes.decode("utf-8")
            return f"{base_url}?n={quote(original_filename)}"
        except (KeyError, TypeError, Exception) as e:
            logger.error(f"Bunkr: Error decrypting URL: {e}")
            return None

    def export(self) -> Generator[str, None, None]:
        logger.info(f"Bunkr: Fetching initial URL: {self.url}")
        initial_res = self.session.get(self.url, allow_redirects=True, timeout=30)
        initial_res.raise_for_status()
        resolved_url = initial_res.url
        logger.debug(f"Bunkr: Resolved URL: {resolved_url}")
        soup = BeautifulSoup(initial_res.text, "lxml")

        # Case 1: We landed on an album page (/a/...).
        if "/a/" in resolved_url:
            links = (
                soup.select('a.image[href^="/f/"]')
                or soup.select('div.grid-images a[href^="/f/"]')
                or soup.select('div#grid-images a[href^="/f/"]')
            )

            if not links:
                logger.warning(
                    "Bunkr: Could not find any file links on the album page."
                )
                return
            logger.info(f"Bunkr: Found {len(links)} items in album.")
            unique_urls = set()
            for link in links:
                viewer_page_url = urljoin(
                    self._get_base_url(resolved_url), link["href"]
                )
                if viewer_page_url in unique_urls:
                    continue
                unique_urls.add(viewer_page_url)
                yield from self._resolve_viewer_page(viewer_page_url)

        # Case 2: We landed on a viewer page (/f/...).
        elif "/f/" in resolved_url:
            logger.debug(f"Bunkr: Processing viewer page directly: {resolved_url}")
            yield from self._resolve_viewer_page(resolved_url)

        # Case 3: We landed directly on a final download page (/file/...).
        elif "/file/" in resolved_url:
            logger.debug(f"Bunkr: Direct file URL found: {resolved_url}")
            yield resolved_url  # Unlikely with current bunkr, but handle if present
        else:
            logger.warning(
                f"Bunkr: Unrecognized URL format after redirect: {resolved_url}"
            )

    def _resolve_viewer_page(self, viewer_url: str) -> Generator[str, None, None]:
        logger.debug(f"Bunkr: Resolving viewer page: {viewer_url}")
        page_res = self.session.get(viewer_url, timeout=30)
        page_res.raise_for_status()
        soup = BeautifulSoup(page_res.text, "lxml")
        download_button = soup.find(
            "a", class_=["btn-main", "ic-download-01"], string="Download"
        )

        if download_button and download_button.get("href"):
            file_page_url = download_button["href"]
            absolute_file_page_url = urljoin(page_res.url, file_page_url)
            logger.debug(f"Bunkr: Found download page URL: {absolute_file_page_url}")
            yield absolute_file_page_url
        else:
            logger.warning(
                f"Bunkr: Failed to find download button/link on viewer page {viewer_url}"
            )

    def download_file(self, file_page_url: str, output_dir: str) -> Optional[str]:
        logger.info(f"Bunkr: Processing download page: {file_page_url}")
        page_res = self.session.get(file_page_url, timeout=30)
        page_res.raise_for_status()
        soup = BeautifulSoup(page_res.text, "lxml")

        download_element = soup.find("a", id="download-btn")
        if not download_element or "data-id" not in download_element.attrs:
            file_id_match = re.search(r"/file/([^/?#]+)", file_page_url)
            if not file_id_match:
                raise ValueError("Could not find file ID (checked element and URL).")
            file_id = file_id_match.group(1)
            logger.debug(f"Bunkr: Extracted file ID from URL: {file_id}")
        else:
            file_id = download_element["data-id"]
            logger.debug(f"Bunkr: Extracted file ID from data-id: {file_id}")

        original_filename = None
        og_title_tag = soup.find("meta", property="og:title")
        if og_title_tag and og_title_tag.get("content"):
            original_filename = unentitify(og_title_tag["content"]).strip()
        if not original_filename:
            script_tag = soup.find("script", string=re.compile(r"var ogname\s*="))
            if script_tag:
                match = re.search(r'var ogname\s*=\s*"(.*?)"', script_tag.string)
                if match:
                    original_filename = unentitify(match.group(1)).strip()

        if not original_filename:
            logger.warning("Bunkr: Could not extract original filename, using default.")
            original_filename = "bunkr_file"

        logger.debug(f"Bunkr: Calling API for file ID: {file_id}")
        api_res = self.session.post(self.API_URL, json={"id": file_id}, timeout=30)
        api_res.raise_for_status()
        api_data = api_res.json()

        final_url = self._solve_encrypted_url(api_data, original_filename)
        if not final_url:
            raise ValueError("Failed to decrypt the download URL.")

        logger.info(f"Bunkr: Downloading '{original_filename}' from {final_url}")
        os.makedirs(output_dir, exist_ok=True)
        save_path = os.path.join(output_dir, original_filename)
        headers = {"Referer": self._get_base_url(file_page_url) + "/"}
        with self.session.get(
            final_url, headers=headers, stream=True, allow_redirects=True, timeout=60
        ) as r:
            r.raise_for_status()
            with open(save_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        logger.info(f"Bunkr: Downloaded '{original_filename}' -> {save_path}")
        return save_path
