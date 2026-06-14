import hashlib
import logging
import os
import re
import time

from collections.abc import Generator
from typing import Any

from megaloader.error_policy import raise_extraction_error, raise_for_api_status
from megaloader.fetcher import Fetcher, Request, SessionConfig
from megaloader.item import DownloadItem
from megaloader.plugin import BasePlugin


logger = logging.getLogger(__name__)

_token_cache: dict[str, str] = {}

# gofile signs every /contents call with a website token: sha256 over the user
# agent, language, account token, a 4-hour time bucket, and a rotating salt that
# gofile ships (obfuscated) in https://gofile.io/dist/js/wt.obf.js. The salt
# changes every few months; override it with GOFILE_SALT when a recording run
# starts returning error-notPremium, which is the symptom of a stale salt.
_WEBSITE_TOKEN_SALT = os.getenv("GOFILE_SALT") or "9844d94d963d30"
_TIME_BUCKET_SECONDS = 14400
_BROWSER_LANG = "en-US"
# The website token hashes this exact user agent, so the request must send the
# same string. session_config() pins it on the session for that reason.
_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"


def parse_content_id(url: str) -> str:
    match = re.search(r"gofile\.io/(?:d|f)/([\w-]+)", url)
    if not match:
        msg = f"Invalid Gofile URL: {url}"
        raise ValueError(msg)
    return match.group(1)


def hash_password(password: str | None) -> str | None:
    if password:
        return hashlib.sha256(password.encode()).hexdigest()
    return None


def website_token(api_token: str) -> str:
    """Recreate gofile's wt.obf.js signature for the current 4-hour bucket."""
    bucket = int(time.time() // _TIME_BUCKET_SECONDS)
    raw = (
        f"{_USER_AGENT}::{_BROWSER_LANG}::{api_token}::{bucket}::{_WEBSITE_TOKEN_SALT}"
    )
    return hashlib.sha256(raw.encode()).hexdigest()


class Gofile(BasePlugin):
    """Extract files from Gofile folders."""

    API_BASE = "https://api.gofile.io"

    def __init__(self, url: str, **options: Any) -> None:
        super().__init__(url, **options)
        self.content_id = parse_content_id(url)
        self.password_hash = hash_password(self.options.get("password"))

    def session_config(self) -> SessionConfig:
        return SessionConfig(headers={"User-Agent": _USER_AGENT})

    def extract(self, fetch: Fetcher) -> Generator[DownloadItem, None, None]:
        api_token = self._get_api_token(fetch)

        api_url = f"{self.API_BASE}/contents/{self.content_id}"
        params: dict[str, str] = {
            "contentFilter": "",
            "sortField": "name",
            "sortDirection": "1",
            "pageSize": "1000",
            "page": "1",
        }

        if self.password_hash:
            params["password"] = self.password_hash
            logger.debug("Using password protection")

        response = fetch(
            Request(
                api_url,
                params=params,
                headers={
                    "Authorization": f"Bearer {api_token}",
                    "X-Website-Token": website_token(api_token),
                    "X-BL": _BROWSER_LANG,
                    "Origin": "https://gofile.io",
                    "Referer": "https://gofile.io/",
                },
            )
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

    def _get_api_token(self, fetch: Fetcher) -> str:
        """Return caller-provided token, cached guest token, or create a new guest account."""
        token = self.options.get("token") or os.getenv("GOFILE_TOKEN")
        if token:
            return str(token)

        if cached := _token_cache.get("gofile"):
            return cached

        accounts_url = f"{self.API_BASE}/accounts"
        response = fetch(Request(accounts_url, method="POST"))
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
