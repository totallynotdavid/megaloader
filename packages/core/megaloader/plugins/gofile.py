import hashlib
import logging
import re

from collections.abc import Generator
from typing import Any

from megaloader.plugin import BasePlugin, Item


logger = logging.getLogger(__name__)


class Gofile(BasePlugin):
    API_URL = "https://api.gofile.io"

    def __init__(self, url: str, **kwargs: Any) -> None:
        super().__init__(url, **kwargs)
        self.content_id = self._get_content_id(url)
        self.password_hash = None
        if pwd := self.options.get("password"):
            self.password_hash = hashlib.sha256(pwd.encode()).hexdigest()

        self._website_token = None
        self._api_token = None

    def _get_content_id(self, url: str) -> str:
        match = re.search(r"gofile\.io/(?:d|f)/([\w-]+)", url)
        if not match:
            raise ValueError("Invalid Gofile URL")
        return match.group(1)

    @property
    def website_token(self) -> str:
        if not self._website_token:
            resp = self.session.get("https://gofile.io/dist/js/global.js", timeout=30)
            resp.raise_for_status()
            if match := re.search(r'\.wt\s*=\s*"([^"]+)"', resp.text):
                self._website_token = match.group(1)
            else:
                raise RuntimeError("Could not find website token")
        return self._website_token

    @property
    def api_token(self) -> str:
        if not self._api_token:
            resp = self.session.post(f"{self.API_URL}/accounts", timeout=30)
            resp.raise_for_status()
            data = resp.json()
            if data.get("status") == "ok":
                self._api_token = data["data"]["token"]
            else:
                raise ConnectionError("Failed to create Gofile account")
        return self._api_token

    def extract(self) -> Generator[Item, None, None]:
        api_url = f"{self.API_URL}/contents/{self.content_id}"
        params = {"wt": self.website_token}
        if self.password_hash:
            params["password"] = self.password_hash

        headers = {"Authorization": f"Bearer {self.api_token}"}

        try:
            response = self.session.get(
                api_url, params=params, headers=headers, timeout=30
            )
            response.raise_for_status()
            data = response.json()

            if data.get("status") != "ok":
                raise ConnectionError(
                    f"Gofile API Error: {data.get('data', {}).get('message')}"
                )

            content = data.get("data", {})
            album_title = content.get("name", self.content_id)
            files = content.get("children", {})

            if not files:
                logger.warning("No files found (Password might be required)")
                return

            for f in files.values():
                if f.get("type") == "file":
                    yield Item(
                        url=f["link"],
                        filename=f["name"],
                        id=f["id"],
                        album=album_title,
                        meta={"size": f.get("size")},
                    )

        except Exception:
            logger.exception("Failed to extract from Gofile")
            raise
