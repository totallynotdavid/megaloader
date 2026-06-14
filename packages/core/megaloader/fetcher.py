import json as jsonlib
import logging
import os

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Protocol

import requests

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from megaloader.error_policy import build_extraction_error


logger = logging.getLogger(__name__)

DEFAULT_HEADERS: dict[str, str] = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}

# When this env var is truthy, the fetcher logs the URL, status, and the first
# chunk of the response body for every failure. Off in production so it never
# leaks credentials, on only when a maintainer is debugging a live extraction.
_LIVE_DEBUG_ENV = "MEGALOADER_LIVE_DEBUG"


def _live_debug_enabled() -> bool:
    return bool(os.environ.get(_LIVE_DEBUG_ENV))


DEFAULT_TIMEOUT: float | tuple[float, float] = 30
RETRY_TOTAL = 2
RETRY_BACKOFF = 0.5


@dataclass(frozen=True)
class Request:
    """A single HTTP request described as data, independent of any HTTP client."""

    url: str
    method: str = "GET"
    params: Mapping[str, Any] | None = None
    json: Any | None = None
    headers: Mapping[str, str] | None = None
    allow_redirects: bool = True


@dataclass(frozen=True)
class Response:
    """An HTTP response reduced to what extractors read: final URL, status, body."""

    url: str
    status_code: int
    text: str
    content: bytes

    def json(self) -> Any:
        return jsonlib.loads(self.text)


@dataclass(frozen=True)
class Cookie:
    name: str
    value: str
    domain: str


@dataclass(frozen=True)
class SessionConfig:
    """Plugin-declared session state (site headers, auth cookies) expressed as data.

    Plugins return this from session_config() instead of touching a session
    directly, which keeps them free of any HTTP-client dependency.
    """

    headers: dict[str, str] = field(default_factory=dict)
    cookies: tuple[Cookie, ...] = ()


class Fetcher(Protocol):
    """Resolves a Request to a Response.

    This is the only seam that performs network I/O. Production code uses
    RequestsFetcher; tests pass a function that returns canned Responses, which
    is enough to exercise a plugin's full traversal offline.
    """

    def __call__(self, request: Request) -> Response: ...


class RequestsFetcher:
    """Production Fetcher backed by a requests.Session.

    Owns retries, the default User-Agent, and the mapping from requests
    failures to ExtractionError. The source label tags those errors with the
    plugin name so downstream policy can attribute them.
    """

    def __init__(
        self,
        source: str,
        *,
        config: SessionConfig | None = None,
        session: requests.Session | None = None,
        timeout: float | tuple[float, float] | None = None,
    ) -> None:
        self._source = source
        self._timeout = timeout if timeout is not None else DEFAULT_TIMEOUT
        # A caller-provided session keeps its own headers; only a session we
        # build here gets the default User-Agent, matching prior behavior.
        self._session = session if session is not None else self._build_session()
        self._apply_config(config or SessionConfig())

    def _build_session(self) -> requests.Session:
        session = requests.Session()
        session.headers.update(DEFAULT_HEADERS)

        retry_strategy = Retry(
            total=RETRY_TOTAL,
            backoff_factor=RETRY_BACKOFF,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)

        return session

    def _apply_config(self, config: SessionConfig) -> None:
        self._session.headers.update(config.headers)
        for cookie in config.cookies:
            self._session.cookies.set(cookie.name, cookie.value, domain=cookie.domain)

    def __call__(self, request: Request) -> Response:
        url = request.url
        try:
            raw = self._session.request(
                request.method,
                url,
                params=dict(request.params) if request.params else None,
                json=request.json,
                headers=dict(request.headers) if request.headers else None,
                allow_redirects=request.allow_redirects,
                timeout=self._timeout,
            )
            raw.raise_for_status()
        except requests.HTTPError as e:
            status = e.response.status_code if e.response is not None else None
            if _live_debug_enabled() and e.response is not None:
                body_preview = e.response.text[:500] if e.response.text else ""
                logger.debug(
                    "LIVE %s %s -> %s body=%r",
                    request.method,
                    url,
                    status,
                    body_preview,
                )
            detail = f"{self._source} request failed ({status}): {url}"
            raise build_extraction_error(
                detail, source=self._source, url=url, http_status=status, cause=e
            ) from e
        except requests.Timeout as e:
            detail = f"{self._source} request timed out: {url}"
            raise build_extraction_error(
                detail, source=self._source, url=url, category="timeout", cause=e
            ) from e
        except requests.ConnectionError as e:
            detail = f"{self._source} connection failed: {url}"
            raise build_extraction_error(
                detail, source=self._source, url=url, category="network", cause=e
            ) from e
        except requests.RequestException as e:
            detail = f"{self._source} request failed: {url}"
            raise build_extraction_error(
                detail, source=self._source, url=url, category="network", cause=e
            ) from e

        return Response(
            url=raw.url,
            status_code=raw.status_code,
            text=raw.text,
            content=raw.content,
        )
