import urllib.parse
from typing import Optional, Type

from .plugin import BasePlugin
from .plugins import (
    get_plugin_class,
    Bunkr,
    PixelDrain,
)

# This allows users to do `from megaloader import Bunkr, download`
__all__ = ["download", "BasePlugin", "Bunkr", "PixelDrain"]


def download(
    url: str,
    output_dir: str,
    *,
    plugin_class: Optional[Type[BasePlugin]] = None,
    **plugin_kwargs,
) -> bool:
    """
    Main download function. Automatically detects the service/plugin based on URL
    or uses a specified plugin class.

    Args:
        url (str): The main URL to download from (album, post, etc.).
        output_dir (str): The local directory to save files.
        plugin_class (type[BasePlugin], optional): Force the use of a specific plugin class.
                                                   If None, it's auto-detected.
        **plugin_kwargs: Additional keyword arguments passed to the plugin's constructor.

    Returns:
        bool: True if the process completed without raising an unhandled exception,
              False if an error occurred.
    """
    try:
        plugin_instance = None
        if plugin_class is not None:
            if not issubclass(plugin_class, BasePlugin):
                raise TypeError(
                    "Provided plugin_class must be a subclass of BasePlugin."
                )
            plugin_instance = plugin_class(url, **plugin_kwargs)
        else:
            parsed_url = urllib.parse.urlparse(url)
            domain = parsed_url.netloc
            if not domain:
                raise ValueError("Invalid URL: Could not parse domain.")
            detected_plugin_class = get_plugin_class(domain)
            if detected_plugin_class is None:
                raise ValueError(f"No plugin found for domain: {domain}")
            plugin_instance = detected_plugin_class(url, **plugin_kwargs)

        print(
            f"[INFO] Using plugin: {plugin_instance.__class__.__name__} for URL: {url}"
        )

        exported_items = list(plugin_instance.export())
        if not exported_items:
            print("[WARNING] No items found to export.")
            return True

        print(f"[INFO] Found {len(exported_items)} items to process.")

        success_count = 0
        for i, item in enumerate(exported_items, 1):
            print(f"[INFO] Processing item {i}/{len(exported_items)}")
            try:
                result = plugin_instance.download_file(item, output_dir)
                if result:
                    success_count += 1
                else:
                    print("[WARNING] Item processing reported failure or skipped.")
            except Exception as e:
                print(f"[ERROR] Error during processing of item {i}: {e}")

        print(
            f"[INFO] Download process finished. Successful items: {success_count}/{len(exported_items)}"
        )
        return True

    except Exception as e:
        print(f"[ERROR] Critical error in main download function: {e}")
        return False
