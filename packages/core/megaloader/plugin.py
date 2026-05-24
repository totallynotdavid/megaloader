import logging

from abc import ABC, abstractmethod
from collections.abc import Generator
from typing import Any, ClassVar

import requests

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from megaloader.error_policy import build_extraction_error
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
    DEFAULT_TIMEOUT: ClassVar[float | tuple[float, float]] = 30
    DEFAULT_RETRY_TOTAL: ClassVar[int] = 2
    DEFAULT_RETRY_BACKOFF: ClassVar[float] = 0.5

    def __init__(
        self,
        url: str,
        *,
        session: requests.Session | None = None,
        timeout: float | tuple[float, float] | None = None,
        **options: Any,
    ) -> None:
        if not url.strip():
            msg = "URL must be a non-empty string"
            raise ValueError(msg)

        self.url = url.strip()
        self.options = options
        self._session: requests.Session | None = session
        self._timeout = timeout if timeout is not None else self.DEFAULT_TIMEOUT

    @property
    def session(self) -> requests.Session:
        """Lazily create session with retry logic and default headers."""
        if self._session is None:
            self._session = self._create_session()
            self._configure_session(self._session)
        return self._session

    @property
    def timeout(self) -> float | tuple[float, float]:
        return self._timeout

    def _create_session(self) -> requests.Session:
        session = requests.Session()
        session.headers.update(self.DEFAULT_HEADERS)

        retry_strategy = Retry(
            total=self.DEFAULT_RETRY_TOTAL,
            backoff_factor=self.DEFAULT_RETRY_BACKOFF,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)

        return session

    def _configure_session(self, session: requests.Session) -> None:  # noqa: B027
        """
        Override to add plugin-specific headers/cookies.

        Example:
            session.headers["Referer"] = f"https://{self.domain}/"
            if api_key := os.getenv("PLUGIN_API_KEY"):
                session.headers["Authorization"] = f"Bearer {api_key}"
        """

    def _request(self, method: str, url: str, **kwargs: Any) -> requests.Response:
        """
        Make an HTTP request and map network/HTTP failures to ExtractionError.

        Handles HTTPError, Timeout, ConnectionError, and other RequestException
        subclasses. Status codes are classified via error_policy.classify_failure.
        Plugins call _get/_post instead of session directly.
        """
        source = type(self).__name__.lower()
        kwargs.setdefault("timeout", self._timeout)
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except requests.HTTPError as e:
            status = e.response.status_code if e.response is not None else None
            detail = f"{source} request failed ({status}): {url}"
            raise build_extraction_error(
                detail, source=source, url=url, http_status=status, cause=e
            ) from e
        except requests.Timeout as e:
            detail = f"{source} request timed out: {url}"
            raise build_extraction_error(
                detail, source=source, url=url, category="timeout", cause=e
            ) from e
        except requests.ConnectionError as e:
            detail = f"{source} connection failed: {url}"
            raise build_extraction_error(
                detail, source=source, url=url, category="network", cause=e
            ) from e
        except requests.RequestException as e:
            detail = f"{source} request failed: {url}"
            raise build_extraction_error(
                detail, source=source, url=url, category="network", cause=e
            ) from e

    def _get(self, url: str, **kwargs: Any) -> requests.Response:
        return self._request("GET", url, **kwargs)

    def _post(self, url: str, **kwargs: Any) -> requests.Response:
        return self._request("POST", url, **kwargs)

    @abstractmethod
    def extract(self) -> Generator[DownloadItem, None, None]:
        """
        Extract downloadable items from the URL.

        Yields items as they're discovered (lazy evaluation).
        Should handle pagination, nested galleries, etc.

        Yields:
            DownloadItem: Each file found at the URL

        Raises:
            ExtractionError: On network/HTTP/parsing failures
        """
