"""
Extract downloadable content metadata from
file hosting platforms. Check the README for a full
list of supported sites.
"""

import logging
import urllib.parse

from typing import Any

from megaloader.exceptions import ExtractionError, UnsupportedDomainError
from megaloader.plugin import Item
from megaloader.plugins import get_plugin_class


# Suppress default logging unless explicitly configured
logging.getLogger(__name__).addHandler(logging.NullHandler())
logger = logging.getLogger(__name__)

__version__ = "0.2.0"
__all__ = ["ExtractionError", "Item", "UnsupportedDomainError", "extract"]


def extract(url: str, **options: Any) -> list[Item]:
    """
    Extract downloadable items from a URL.

    Args:
        url: The URL to extract from
        **options: Plugin-specific options (password, etc.)

    Returns:
        List of Item objects containing download metadata
    """
    if not url or not url.strip():
        raise ValueError("URL cannot be empty")

    url = url.strip()
    parsed_url = urllib.parse.urlparse(url)

    if not parsed_url.netloc:
        raise ValueError("Invalid URL: Could not parse domain")

    plugin_cls = get_plugin_class(parsed_url.netloc)
    if plugin_cls is None:
        raise UnsupportedDomainError(parsed_url.netloc)

    try:
        logger.info("Extracting from %s using %s", url, plugin_cls.__name__)
        plugin = plugin_cls(url, **options)
        # We convert generator to list here to satisfy the "list" return type
        # expected by consumers wanting to check len(items) immediately.
        items = list(plugin.extract())
        logger.info("Extracted %d items", len(items))
        return items
    except (UnsupportedDomainError, ValueError, TypeError):
        raise
    except Exception as e:
        msg = f"Failed to extract items from {url}"
        raise ExtractionError(msg) from e
