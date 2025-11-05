import logging
import os
import re
import time

from collections.abc import Generator
from typing import Any
from urllib.parse import urljoin, urlparse

import requests

from bs4 import BeautifulSoup

from megaloader.plugin import BasePlugin, Item


logger = logging.getLogger(__name__)

INVALID_FILENAME_CHARS = r'[<>:"/\\|?*]'


class Cyberdrop(BasePlugin):
    """
    Plugin for downloading files from Cyberdrop.
    Supports both album links (/a/...) and single file links (/f/...).
    """

    API_BASE_URL = "https://api.cyberdrop.cr/api/file"
    BASE_URL = "https://cyberdrop.cr"

    def __init__(
        self,
        url: str,
        rate_limit_seconds: float = 1.0,
        **kwargs: Any,
    ) -> None:
        super().__init__(url, **kwargs)
        self.rate_limit_seconds = rate_limit_seconds
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/json, text/html, */*",
            },
        )
        # Timestamp of the last API call. Use 0.0 for the first run.
        self._last_api_call_time: float = 0.0

    def _sanitize_name(self, name: str) -> str:
        """Removes illegal characters from a filename or directory name."""
        return re.sub(INVALID_FILENAME_CHARS, "_", name).strip()

    def _get_file_info(self, file_id: str) -> dict[str, Any] | None:
        """
        Fetches file metadata from the Cyberdrop API, respecting rate limits.
        This method ensures there is at least `rate_limit_seconds` between calls.
        """
        now = time.monotonic()
        time_since_last_call = now - self._last_api_call_time

        if time_since_last_call < self.rate_limit_seconds:
            sleep_duration = self.rate_limit_seconds - time_since_last_call
            logger.debug(f"Rate limiting: sleeping for {sleep_duration:.2f} seconds.")
            time.sleep(sleep_duration)

        api_url = f"{self.API_BASE_URL}/info/{file_id}"
        try:
            response = self.session.get(api_url, timeout=30)
            response.raise_for_status()

            data = response.json()
            if not isinstance(data, dict):
                logger.error(f"API response for {file_id} is not a valid JSON object.")
                return None

            if not data.get("name") or not data.get("auth_url"):
                logger.error(f"Invalid metadata for file ID {file_id}: {data}")
                return None
            return data
        except requests.RequestException as e:
            logger.exception(f"Failed to get file info for ID {file_id}: {e}")
        except ValueError:
            logger.exception(f"Failed to decode JSON from file info for ID {file_id}")
        finally:
            self._last_api_call_time = time.monotonic()
        return None

    def export(self) -> Generator[Item, None, None]:
        """Extracts downloadable items from a Cyberdrop URL."""
        logger.info(f"Processing Cyberdrop URL: {self.url}")
        parsed_url = urlparse(self.url)

        if parsed_url.path.startswith("/a/"):
            yield from self._export_album()
        elif parsed_url.path.startswith("/f/"):
            yield from self._export_single_file()
        else:
            logger.warning(f"Unrecognized Cyberdrop URL format: {self.url}")

    def _export_album(self) -> Generator[Item, None, None]:
        """Extracts all items from an album page."""
        try:
            response = self.session.get(self.url, timeout=30)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.exception(f"Failed to fetch album page {self.url}: {e}")
            return

        soup = BeautifulSoup(response.text, "html.parser")

        title_el = soup.find("h1", id="title")
        album_title = (
            self._sanitize_name(title_el.text) if title_el else "cyberdrop_album"
        )
        logger.info(f"Found album: {album_title}")

        file_links = soup.select("a.file[href], a#file[href]")
        if not file_links:
            logger.warning("No file links found on album page.")
            return

        logger.info(f"Found {len(file_links)} files in album. Fetching metadata...")
        for link in file_links:
            file_url = urljoin(self.BASE_URL, str(link["href"]))
            file_id_match = re.search(r"/f/(\w+)", file_url)
            if not file_id_match:
                continue

            file_id = file_id_match.group(1)
            info = self._get_file_info(file_id)
            if info:
                yield Item(
                    url=info["auth_url"],
                    filename=self._sanitize_name(info["name"]),
                    album_title=album_title,
                    file_id=file_id,
                )

    def _export_single_file(self) -> Generator[Item, None, None]:
        """Extracts an item from a single file page."""
        file_id_match = re.search(r"/f/(\w+)", self.url)
        if not file_id_match:
            logger.error(f"Could not extract file ID from URL: {self.url}")
            return

        file_id = file_id_match.group(1)
        info = self._get_file_info(file_id)
        if info:
            yield Item(
                url=info["auth_url"],
                filename=self._sanitize_name(info["name"]),
                file_id=file_id,
            )

    def download_file(self, item: Item, output_dir: str) -> bool:
        """Downloads a single file from Cyberdrop."""
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, item.filename)

        if os.path.exists(output_path):
            logger.info(f"File already exists: {item.filename}")
            return True

        try:
            auth_response = self.session.get(item.url, timeout=30)
            auth_response.raise_for_status()
            response_json = auth_response.json()
            direct_url = response_json.get("url")

            if not direct_url:
                logger.error(
                    f"Could not get direct download URL for {item.filename}. API response: {response_json}",
                )
                return False

            logger.debug(f"Downloading {item.filename} from direct URL")
            with self.session.get(direct_url, stream=True, timeout=180) as response:
                response.raise_for_status()
                with open(output_path, "wb") as f:
                    f.writelines(response.iter_content(chunk_size=8192))

            logger.info(f"Downloaded: {item.filename}")
            return True
        except (requests.RequestException, ValueError, KeyError) as e:
            logger.exception(f"Download failed for {item.filename}: {e}")
            if os.path.exists(output_path):
                os.remove(output_path)
            return False
