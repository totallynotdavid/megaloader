"""
Megaloader - This project will make you smile. It allows you to use
some download plugins for many websites. Check the README for a full
list of supported sites.

Basic usage:
    ```python
    from megaloader import download

    success = download("https://bunkr.si/a/example", "./downloads/")
    if success:
        print("Download completed")
    ```

Advanced usage with specific plugin:
    ```python
    from megaloader import Bunkr

    plugin = Bunkr("https://bunkr.si/a/example")
    items = list(plugin.export())
    for item in items:
        plugin.download_file(item, "./downloads/")
    ```
"""

import logging
import os
import re
import urllib.parse

from typing import Any, Optional

from megaloader.plugin import BasePlugin, Item
from megaloader.plugins import (
    Bunkr,
    Cyberdrop,
    Fapello,
    Gofile,
    PixelDrain,
    ThothubTO,
    get_plugin_class,
)


# Suppress default logging unless explicitly configured
logging.getLogger(__name__).addHandler(logging.NullHandler())

__version__ = "0.1.0"
__all__ = [
    "BasePlugin",
    "Bunkr",
    "Cyberdrop",
    "Fapello",
    "Gofile",
    "Item",
    "PixelDrain",
    "ThothubTO",
    "download",
]

INVALID_DIR_CHARS = r'[<>:"/\\|?*]'


def download(
    url: str,
    output_dir: str,
    *,
    plugin_class: Optional[type[BasePlugin]] = None,
    create_album_subdirs: bool = True,
    **kwargs: Any,
) -> bool:
    """
    Download files from a URL using appropriate plugin.

    Args:
        url: The URL to download from
        output_dir: Directory to save files to
        plugin_class: Specific plugin to use (auto-detected if None)
        create_album_subdirs: If True, create a sub-directory for albums
        **kwargs: Additional options passed to the plugin

    Returns:
        True if at least one file was successfully downloaded, False otherwise

    Raises:
        ValueError: If URL is invalid or no plugin found for domain
        TypeError: If plugin_class is not a BasePlugin subclass
    """
    logger = logging.getLogger(__name__)

    try:
        if plugin_class is not None:
            if not issubclass(plugin_class, BasePlugin):
                raise TypeError("plugin_class must be a BasePlugin subclass")
            plugin = plugin_class(url, **kwargs)
        else:
            parsed_url = urllib.parse.urlparse(url)
            if not parsed_url.netloc:
                raise ValueError("Invalid URL: Could not parse domain")

            plugin_cls = get_plugin_class(parsed_url.netloc)
            if plugin_cls is None:
                raise ValueError(f"No plugin found for domain: {parsed_url.netloc}")
            plugin = plugin_cls(url, **kwargs)

        logger.info(f"Using {plugin.__class__.__name__} for {url}")

        items = list(plugin.export())
        if not items:
            logger.info("No items found to download")
            return True

        logger.info(f"Processing {len(items)} items")
        success_count = 0

        for i, item in enumerate(items, 1):
            try:
                item_output_dir = output_dir
                if create_album_subdirs and item.album_title:
                    sane_album_title = re.sub(
                        INVALID_DIR_CHARS, "_", item.album_title
                    ).strip()
                    if sane_album_title:
                        item_output_dir = os.path.join(output_dir, sane_album_title)

                result = plugin.download_file(item, item_output_dir)
                if result:
                    success_count += 1
                    logger.debug(f"Downloaded {i}/{len(items)}: {item.filename}")
                else:
                    logger.warning(
                        f"Failed to download {i}/{len(items)}: {item.filename}"
                    )
            except Exception as e:
                logger.error(f"Error downloading item {i}: {e}")

        logger.info(f"Completed: {success_count}/{len(items)} successful")
        return success_count > 0

    except Exception as e:
        logger.error(f"Download failed: {e}")
        return False
