import logging

from abc import ABC, abstractmethod
from collections.abc import Generator
from dataclasses import dataclass, field
from typing import Any

import requests


logger = logging.getLogger(__name__)


@dataclass
class Item:
    """Represents a downloadable item with metadata."""

    url: str
    filename: str
    album: str | None = None
    id: str | None = None
    meta: dict[str, Any] | None = field(default=None)


class BasePlugin(ABC):
    """
    Base class for all megaloader plugins.
    """

    DEFAULT_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }

    def __init__(self, url: str, **kwargs: Any) -> None:
        if not url.strip():
            raise ValueError("URL must be a non-empty string")
        self.url = url.strip()
        self.options = kwargs
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """Creates a requests session with default headers."""
        session = requests.Session()
        session.headers.update(self.DEFAULT_HEADERS)
        return session

    @abstractmethod
    def extract(self) -> Generator[Item, None, None]:
        """
        Extract downloadable items from the URL.

        Yields:
            Item: Each downloadable file found at the URL
        """
