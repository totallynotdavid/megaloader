"""
Megaloader - Extract downloadable content metadata from file hosting platforms.

Basic usage:
    import megaloader as mgl

    for item in mgl.extract(url):
        print(item.url, item.filename)

    # With plugin-specific options
    items = mgl.extract(url, password="secret")
    items = mgl.extract(url, session_id="cookie_value")
"""

import logging
import urllib.parse

from collections.abc import Generator
from typing import Any

from megaloader.exceptions import ExtractionError, UnsupportedDomainError
from megaloader.item import DownloadItem
from megaloader.plugins import get_plugin_class


logging.getLogger(__name__).addHandler(logging.NullHandler())
logger = logging.getLogger(__name__)

__version__ = "0.2.0"
__all__ = ["DownloadItem", "ExtractionError", "UnsupportedDomainError", "extract"]


def extract(url: str, **options: Any) -> Generator[DownloadItem, None, None]:
    """
    Extract downloadable items from a URL.

    Returns a generator that yields items lazily as they're discovered.
    Network requests happen during iteration, not at call time.

    Args:
        url: The source URL to extract from
        **options: Plugin-specific options:
            - password: str (Gofile)
            - session_id: str (Fanbox, Pixiv)
            - api_key: str (Rule34)
            - user_id: str (Rule34)

    Yields:
        DownloadItem: Metadata for each downloadable file

    Raises:
        ValueError: Invalid URL format
        UnsupportedDomainError: No plugin available for domain
        ExtractionError: Network or parsing failure

    Example:
        >>> for item in extract("https://pixeldrain.com/l/abc123"):
        ...     download_file(item.download_url, item.filename)
    """
    if not url or not url.strip():
        raise ValueError("URL cannot be empty")

    url = url.strip()
    parsed = urllib.parse.urlparse(url)

    if not parsed.netloc:
        raise ValueError(f"Invalid URL: Could not parse domain from '{url}'")

    plugin_class = get_plugin_class(parsed.netloc)
    if plugin_class is None:
        raise UnsupportedDomainError(parsed.netloc)

    logger.debug(
        "Initializing %s for domain '%s'", plugin_class.__name__, parsed.netloc
    )

    try:
        plugin = plugin_class(url, **options)
        yield from plugin.extract()
    except (UnsupportedDomainError, ValueError):
        raise
    except Exception as e:
        logger.debug("Extraction failed for %s: %s", url, e, exc_info=True)
        raise ExtractionError(f"Failed to extract from {url}: {e}") from e
