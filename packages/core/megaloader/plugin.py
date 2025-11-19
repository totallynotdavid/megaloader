import logging

from abc import ABC, abstractmethod
from collections.abc import Generator
from typing import Any, ClassVar

import requests

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from megaloader.item import DownloadItem


logger = logging.getLogger(__name__)


class BasePlugin(ABC):
    """
    Base class for site-specific extractors.

    Credential handling convention:
    1. Explicit **kwargs take precedence (e.g., password="secret")
    2. Environment variables as fallback (PLUGIN_NAME_*)
    3. Fail gracefully if required credentials missing

    Subclasses should override _configure_session() to add:
    - Authentication headers/cookies
    - Site-specific headers (Referer, Origin)
    """

    DEFAULT_HEADERS: ClassVar[dict[str, str]] = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }

    def __init__(self, url: str, **options: Any) -> None:
        if not url.strip():
            msg = "URL must be a non-empty string"
            raise ValueError(msg)

        self.url = url.strip()
        self.options = options
        self._session: requests.Session | None = None

    @property
    def session(self) -> requests.Session:
        """Lazily create session with retry logic and default headers."""
        if self._session is None:
            self._session = self._create_session()
            self._configure_session(self._session)
        return self._session

    def _create_session(self) -> requests.Session:
        """Create session with retry strategy for transient failures."""
        session = requests.Session()
        session.headers.update(self.DEFAULT_HEADERS)

        # Retry on common transient errors
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)

        return session

    def _configure_session(self, session: requests.Session) -> None:
        """
        Override to add plugin-specific headers/cookies.

        Example:
            session.headers["Referer"] = f"https://{self.domain}/"
            if api_key := os.getenv("PLUGIN_API_KEY"):
                session.headers["Authorization"] = f"Bearer {api_key}"
        """

    @abstractmethod
    def extract(self) -> Generator[DownloadItem, None, None]:
        """
        Extract downloadable items from the URL.

        Yields items as they're discovered (lazy evaluation).
        Should handle pagination, nested galleries, etc.

        Yields:
            DownloadItem: Each file found at the URL

        Raises:
            ExtractionError: On network/parsing failures
        """
