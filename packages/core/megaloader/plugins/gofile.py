import hashlib
import logging
import re
from collections.abc import Generator
from typing import Any

from megaloader.item import DownloadItem
from megaloader.plugin import BasePlugin

logger = logging.getLogger(__name__)


class Gofile(BasePlugin):
    """Extract files from Gofile folders."""

    API_BASE = "https://api.gofile.io"

    def __init__(self, url: str, **options: Any) -> None:
        super().__init__(url, **options)
        self.content_id = self._parse_content_id(url)
        self.password_hash = self._hash_password(self.options.get("password"))

    def _parse_content_id(self, url: str) -> str:
        """Extract content ID from URL."""
        match = re.search(r"gofile\.io/(?:d|f)/([\w-]+)", url)
        if not match:
            raise ValueError(f"Invalid Gofile URL: {url}")
        return match.group(1)

    def _hash_password(self, password: str | None) -> str | None:
        """Hash password for API if provided."""
        if password:
            return hashlib.sha256(password.encode()).hexdigest()
        return None

    def extract(self) -> Generator[DownloadItem, None, None]:
        # Get required tokens
        website_token = self._get_website_token()
        api_token = self._create_account()

        # Build API request
        api_url = f"{self.API_BASE}/contents/{self.content_id}"
        params = {"wt": website_token}
        
        if self.password_hash:
            params["password"] = self.password_hash
            logger.debug("Using password protection")

        headers = {"Authorization": f"Bearer {api_token}"}

        # Fetch content
        response = self.session.get(api_url, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        
        data = response.json()

        if data.get("status") != "ok":
            error_msg = data.get("data", {}).get("message", "Unknown error")
            raise RuntimeError(f"Gofile API error: {error_msg}")

        content = data.get("data", {})
        collection_name = content.get("name", self.content_id)
        files = content.get("children", {})

        if not files:
            logger.warning("No files found (password may be required)")
            return

        for file_data in files.values():
            if file_data.get("type") == "file":
                yield DownloadItem(
                    download_url=file_data["link"],
                    filename=file_data["name"],
                    source_id=file_data["id"],
                    collection_name=collection_name,
                    size_bytes=file_data.get("size"),
                )

    def _get_website_token(self) -> str:
        """Extract website token from JS file."""
        response = self.session.get("https://gofile.io/dist/js/global.js", timeout=30)
        response.raise_for_status()
        
        if match := re.search(r'\.wt\s*=\s*"([^"]+)"', response.text):
            return match.group(1)
        
        raise RuntimeError("Could not extract Gofile website token")

    def _create_account(self) -> str:
        """Create temporary account and return API token."""
        response = self.session.post(f"{self.API_BASE}/accounts", timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get("status") == "ok":
            return data["data"]["token"]
        
        raise RuntimeError("Failed to create Gofile guest account")
