import hashlib
import logging
import os
import re

from collections.abc import Generator
from typing import Any, Optional

import requests

from megaloader.plugin import BasePlugin, Item


logger = logging.getLogger(__name__)


class Gofile(BasePlugin):
    """
    Plugin for downloading files from Gofile.io links.
    Supports password-protected folders. To use, pass the password as a
    keyword argument: `download(url, dir, password="your_password")`.
    """

    API_URL = "https://api.gofile.io"

    def __init__(self, url: str, **kwargs: Any) -> None:
        super().__init__(url, **kwargs)
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        )

        self.content_id = self._get_content_id_from_url(url)
        self.password_hash: Optional[str] = None

        password = self._config.get("password")
        if password and isinstance(password, str):
            logger.debug("Password provided, generating SHA256 hash.")
            self.password_hash = hashlib.sha256(password.encode()).hexdigest()

        # Placeholders for lazy-loaded tokens
        self._website_token: Optional[str] = None
        self._api_token: Optional[str] = None

    def _get_content_id_from_url(self, url: str) -> str:
        """Extracts the content ID from a Gofile URL."""
        match = re.search(r"gofile\.io/(?:d|f)/([\w-]+)", url)
        if not match:
            raise ValueError("Invalid Gofile URL. Could not extract content ID.")
        return match.group(1)

    @property
    def website_token(self) -> str:
        """Lazily fetches the dynamic website token from Gofile's JavaScript."""
        if self._website_token is None:
            logger.debug("Fetching dynamic website token...")
            try:
                js_url = "https://gofile.io/dist/js/global.js"
                response = self.session.get(js_url, timeout=30)
                response.raise_for_status()

                # Use regex to find the '.wt = "..."' assignment
                match = re.search(r'\.wt\s*=\s*"([^"]+)"', response.text)
                if not match:
                    raise RuntimeError("Could not find website token in global.js.")

                self._website_token = match.group(1)
                logger.debug(
                    f"Successfully fetched website token: {self._website_token}"
                )
            except (requests.RequestException, RuntimeError) as e:
                raise ConnectionError(f"Failed to get Gofile website token: {e}") from e
        return self._website_token

    @property
    def api_token(self) -> str:
        """Lazily creates an anonymous account to get a bearer API token."""
        if self._api_token is None:
            logger.debug("API token not found, creating a new anonymous account...")
            try:
                # The /accounts endpoint creates a temporary account and returns a token.
                response = self.session.post(f"{self.API_URL}/accounts", timeout=30)
                response.raise_for_status()
                data = response.json()

                if data.get("status") != "ok" or "token" not in data.get("data", {}):
                    raise ConnectionError(
                        "Failed to create a Gofile account to get API token."
                    )

                self._api_token = data["data"]["token"]
                logger.debug("Successfully acquired new API bearer token.")
            except (requests.RequestException, ValueError, KeyError) as e:
                raise ConnectionError(
                    f"Failed to get a valid Gofile API token: {e}"
                ) from e
        return self._api_token

    def export(self) -> Generator[Item, None, None]:
        """Fetches the content list of the Gofile folder using the authenticated API."""
        api_url = f"{self.API_URL}/contents/{self.content_id}"
        params = {"wt": self.website_token}
        headers = {"Authorization": f"Bearer {self.api_token}"}

        if self.password_hash:
            params["password"] = self.password_hash

        try:
            logger.info(f"Fetching content for Gofile ID: {self.content_id}")
            response = self.session.get(
                api_url, params=params, headers=headers, timeout=30
            )
            response.raise_for_status()
            data = response.json()

            status = data.get("status")
            if status != "ok":
                error_msg = data.get("data", {}).get(
                    "message", f"Unknown error: {status}"
                )
                raise ConnectionError(f"Gofile API returned an error: {error_msg}")

            content_data = data.get("data")
            if not content_data:
                raise ValueError("Gofile API returned an empty data object.")

            album_title = content_data.get("name", self.content_id)

            if "children" not in content_data:
                logger.warning(
                    f"No downloadable files found in Gofile folder '{album_title}'. A password may be required."
                )
                return

            files = content_data["children"]
            logger.info(f"Found {len(files)} files in folder '{album_title}'.")
            for file_info in files.values():
                if file_info.get("type") == "file":
                    yield Item(
                        url=file_info["link"],
                        filename=file_info["name"],
                        file_id=file_info["id"],
                        album_title=album_title,
                        metadata={"size": file_info.get("size")},
                    )

        except (requests.RequestException, ValueError, KeyError) as e:
            logger.error(f"Failed to export from Gofile: {e}")
            raise

    def download_file(self, item: Item, output_dir: str) -> bool:
        """Downloads a single file from Gofile, using the auth token as a cookie."""
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, item.filename)

        if os.path.exists(output_path):
            logger.info(f"File already exists: {item.filename}")
            return True

        # Gofile links require the account token to be sent as a cookie.
        headers = {"Cookie": f"accountToken={self.api_token}"}

        try:
            logger.debug(f"Downloading: {item.url}")
            with self.session.get(
                item.url, headers=headers, stream=True, timeout=180
            ) as response:
                response.raise_for_status()
                with open(output_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
            logger.info(f"Downloaded: {item.filename}")
            return True
        except requests.RequestException as e:
            logger.error(f"Download failed for {item.filename}: {e}")
            if os.path.exists(output_path):
                os.remove(output_path)
            return False
