import logging
import urllib.parse

from collections.abc import Generator
from typing import Any

import requests

from megaloader.error_policy import build_extraction_error
from megaloader.exceptions import ExtractionError, UnsupportedDomainError
from megaloader.fetcher import RequestsFetcher
from megaloader.item import DownloadItem
from megaloader.plugin import BasePlugin
from megaloader.plugins.registry import get_plugin_by_name, get_plugin_for_domain


logging.getLogger(__name__).addHandler(logging.NullHandler())
logger = logging.getLogger(__name__)


def extract(
    url: str,
    *,
    plugin: str | type[BasePlugin] | None = None,
    session: requests.Session | None = None,
    timeout: float | tuple[float, float] | None = None,
    **options: Any,
) -> Generator[DownloadItem, None, None]:
    """
    Extract downloadable items from a URL.

    Returns a generator that yields items lazily as they're discovered.
    Network requests happen during iteration, not at call time.

    Args:
        url: The source URL to extract from.
        plugin: Optional plugin override (name or plugin class).
        session: Optional caller-provided requests.Session.
        timeout: Optional per-extraction timeout override.
        **options: Plugin-specific options.

    Yields:
        DownloadItem: Metadata for each downloadable file

    Raises:
        ValueError: Invalid URL or plugin override.
        UnsupportedDomainError: No plugin available for domain.
        ExtractionError: Network/API/parsing extraction failures.

    Example:
        >>> for item in extract("https://pixeldrain.com/l/abc123"):
        ...     print(item.download_url, item.filename)
    """
    if not url or not url.strip():
        msg = "URL cannot be empty"
        raise ValueError(msg)

    url = url.strip()
    parsed = urllib.parse.urlparse(url)

    if not parsed.netloc:
        msg = f"Invalid URL: Could not parse domain from '{url}'"
        raise ValueError(msg)

    plugin_class: type[BasePlugin] | None
    if isinstance(plugin, str):
        plugin_class = get_plugin_by_name(plugin)
        if plugin_class is None:
            msg = f"Unknown plugin name: {plugin}"
            raise ValueError(msg)
    elif isinstance(plugin, type):
        if not issubclass(plugin, BasePlugin):
            msg = "plugin class must inherit from BasePlugin"
            raise TypeError(msg)
        plugin_class = plugin
    else:
        plugin_class = get_plugin_for_domain(parsed.netloc)

    if plugin_class is None:
        raise UnsupportedDomainError(parsed.netloc)

    logger.debug("Initializing %s for domain %r", plugin_class.__name__, parsed.netloc)

    try:
        extractor = plugin_class(url, **options)
        fetch = RequestsFetcher(
            extractor.source,
            config=extractor.session_config(),
            session=session,
            timeout=timeout,
        )
        yield from extractor.extract(fetch)
    except (ExtractionError, UnsupportedDomainError, ValueError):
        raise
    except Exception as e:
        logger.debug(
            "Unexpected error from %s for %r: %r",
            plugin_class.__name__,
            url,
            e,
            exc_info=True,
        )
        detail = f"Unexpected error from {plugin_class.__name__}: {e}"
        raise build_extraction_error(
            detail,
            source=plugin_class.__name__.lower(),
            url=url,
            category="unknown",
            cause=e,
        ) from e
