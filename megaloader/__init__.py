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
import re
import urllib.parse

from pathlib import Path
from typing import Any

from megaloader.plugin import BasePlugin, Item
from megaloader.plugins import (
    Bunkr,
    Cyberdrop,
    Fanbox,
    Fapello,
    Gofile,
    PixelDrain,
    ThothubTO,
    get_plugin_class,
)


# Suppress default logging unless explicitly configured
logging.getLogger(__name__).addHandler(logging.NullHandler())

logger = logging.getLogger(__name__)

__version__ = "0.1.0"
__all__ = [
    "BasePlugin",
    "Bunkr",
    "Cyberdrop",
    "Fanbox",
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
    plugin_class: type[BasePlugin] | None = None,
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

    def _validate_url(url: str) -> type[BasePlugin]:
        parsed_url = urllib.parse.urlparse(url)
        if not parsed_url.netloc:
            msg = "Invalid URL: Could not parse domain"
            raise ValueError(msg)

        plugin_cls = get_plugin_class(parsed_url.netloc)
        if plugin_cls is None:
            msg = f"No plugin found for domain: {parsed_url.netloc}"
            raise ValueError(msg)
        return plugin_cls

    def _validate_plugin_class(plugin_class: type) -> None:
        if not issubclass(plugin_class, BasePlugin):
            msg = "plugin_class must be a BasePlugin subclass"
            raise TypeError(msg)

    try:
        if plugin_class is not None:
            _validate_plugin_class(plugin_class)
            plugin = plugin_class(url, **kwargs)
        else:
            plugin_cls = _validate_url(url)
            plugin = plugin_cls(url, **kwargs)

        logger.info("Using %s for %s", plugin.__class__.__name__, url)

        items = list(plugin.export())
        if not items:
            logger.info("No items found to download")
            return True

        logger.info("Processing %d items", len(items))
        success_count = _process_items(
            plugin,
            items,
            output_dir,
            create_album_subdirs=create_album_subdirs,
        )

    except Exception:
        logger.exception("Download failed")
        return False
    else:
        logger.info("Completed: %d/%d successful", success_count, len(items))
        return success_count > 0


def _process_items(
    plugin: BasePlugin,
    items: list[Item],
    output_dir: str,
    *,
    create_album_subdirs: bool,
) -> int:
    success_count = 0
    for i, item in enumerate(items, 1):
        try:
            item_output_dir = output_dir
            if create_album_subdirs and item.album_title:
                sane_album_title = re.sub(
                    INVALID_DIR_CHARS,
                    "_",
                    item.album_title,
                ).strip()
                if sane_album_title:
                    item_output_dir = str(Path(output_dir) / sane_album_title)

            result = plugin.download_file(item, item_output_dir)
            if result:
                success_count += 1
                logger.debug("Downloaded %d/%d: %s", i, len(items), item.filename)
            else:
                logger.warning(
                    "Failed to download %d/%d: %s",
                    i,
                    len(items),
                    item.filename,
                )
        except Exception:
            logger.exception("Error downloading item %d", i)
    return success_count
