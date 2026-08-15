import logging
import os

from abc import ABC, abstractmethod
from collections.abc import Generator
from typing import Any

from megaloader.fetcher import Fetcher, SessionConfig
from megaloader.item import DownloadItem


logger = logging.getLogger(__name__)


class BasePlugin(ABC):
    """Base class for site-specific extractors.

    A plugin performs no network I/O of its own. The engine resolves the URL to
    a plugin, builds a Fetcher, and passes it to extract(). Plugins describe
    each request as a Request and read back a Response, so parsing and traversal
    stay testable offline by substituting a fake Fetcher.

    Credential handling convention, implemented by option():
    1. Explicit kwargs take precedence (e.g. password="secret").
    2. Environment variables as fallback (PLUGIN_*).

    Subclasses override session_config() to declare site headers and auth
    cookies the fetcher should apply.
    """

    def __init__(self, url: str, **options: Any) -> None:
        if not url.strip():
            msg = "URL must be a non-empty string"
            raise ValueError(msg)

        self.url = url.strip()
        self.options = options

    def option(self, name: str, *, env: str | None = None) -> str | None:
        """Read a credential-style option, falling back to its environment variable."""
        value = self.options.get(name)
        if value:
            return str(value)
        if env and (from_env := os.getenv(env)):
            return from_env
        return None

    @property
    def source(self) -> str:
        """Lowercase plugin name used to tag extraction errors."""
        return type(self).__name__.lower()

    def session_config(self) -> SessionConfig:
        """Override to declare site headers and auth cookies for the fetcher."""
        return SessionConfig()

    @abstractmethod
    def extract(self, fetch: Fetcher) -> Generator[DownloadItem, None, None]:
        """Yield downloadable items, fetching pages lazily through fetch.

        Yields items as they're discovered. Handles pagination, nested
        galleries, and so on by issuing further requests through fetch.

        Raises:
            ExtractionError: On network/HTTP/parsing failures.
        """
