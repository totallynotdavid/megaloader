import hashlib
import logging
import os
import re

from collections.abc import Generator
from typing import Any

from megaloader.error_policy import raise_extraction_error, raise_for_api_status
from megaloader.item import DownloadItem
from megaloader.plugin import BasePlugin


logger = logging.getLogger(__name__)

_token_cache: dict[str, str] = {}


class Gofile(BasePlugin):
    """Extract files from Gofile folders."""

    API_BASE = "https://api.gofile.io"

    def __init__(self, url: str, **options: Any) -> None:
        super().__init__(url, **options)
        self.content_id = self._parse_content_id(url)
        self.password_hash = self._hash_password(self.options.get("password"))

    def _parse_content_id(self, url: str) -> str:
        match = re.search(r"gofile\.io/(?:d|f)/([\w-]+)", url)
        if not match:
            msg = f"Invalid Gofile URL: {url}"
            raise ValueError(msg)
        return match.group(1)

    def _hash_password(self, password: str | None) -> str | None:
        if password:
            return hashlib.sha256(password.encode()).hexdigest()
        return None

    def extract(self) -> Generator[DownloadItem, None, None]:
        website_token = self._get_website_token()
        api_token = self._get_api_token()

        api_url = f"{self.API_BASE}/contents/{self.content_id}"
        params: dict[str, str] = {"wt": website_token}

        if self.password_hash:
            params["password"] = self.password_hash
            logger.debug("Using password protection")

        response = self._get(
            api_url,
            params=params,
            headers={
                "Authorization": f"Bearer {api_token}",
                "X-Website-Token": website_token,
            },
        )

        data = response.json()
        raise_for_api_status(
            "gofile",
            api_url,
            data.get("status", "unknown"),
            message=data.get("data", {}).get("message"),
        )

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
        config_url = "https://gofile.io/dist/js/config.js"
        response = self._get(config_url)

        if match := re.search(r'appdata\.wt\s*=\s*"([^"]+)"', response.text):
            return match.group(1)

        raise_extraction_error(
            "Could not extract Gofile website token",
            source="gofile",
            url=config_url,
            category="protocol",
        )

    def _get_api_token(self) -> str:
        """Return caller-provided token, cached guest token, or create a new guest account."""
        token = self.options.get("token") or os.getenv("GOFILE_TOKEN")
        if token:
            return str(token)

        if cached := _token_cache.get("gofile"):
            return cached

        accounts_url = f"{self.API_BASE}/accounts"
        response = self._post(accounts_url)
        data = response.json()

        status = data.get("status", "unknown")
        if status != "ok":
            raise_extraction_error(
                f"Failed to create Gofile guest account: {status}",
                source="gofile",
                url=accounts_url,
                provider_status=status,
            )

        api_token = str(data["data"]["token"])
        _token_cache["gofile"] = api_token
        return api_token
