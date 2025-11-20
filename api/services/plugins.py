import logging

from megaloader.plugin import Item
from megaloader.plugins import get_plugin_class
from models import FileInfo

from api.services.utils import MAX_FILE_COUNT, extract_domain, get_file_size


logger = logging.getLogger(__name__)


def detect_plugin(url: str) -> tuple[bool, str | None, str]:
    """Detect if URL is supported. Returns (is_supported, plugin_name, domain)."""
    domain = extract_domain(url)
    try:
        plugin_class = get_plugin_class(url)
        return (
            (True, plugin_class.__name__, domain)
            if plugin_class
            else (False, None, domain)
        )
    except Exception:
        logger.exception("Plugin detection failed")
        return False, None, domain


def get_items_info(
    plugin_class: type, url: str
) -> tuple[list[Item], int, list[FileInfo]]:
    """Get items from plugin and calculate total size."""
    plugin = plugin_class(url)
    items = list(plugin.extract())

    if not items:
        msg = "No downloadable items found"
        raise ValueError(msg)
    if len(items) > MAX_FILE_COUNT:
        msg = f"Too many files ({len(items)}). Maximum is {MAX_FILE_COUNT}"
        raise ValueError(msg)

    logger.info("Found %d items", len(items))

    total_size = 0
    file_infos = []

    for item in items:
        headers = None
        if hasattr(item, "meta") and item.meta and "referer" in item.meta:
            headers = {"Referer": item.meta["referer"]}

        size = get_file_size(item.url, headers)
        total_size += size
        file_infos.append(
            FileInfo(
                filename=item.filename,
                size_bytes=size,
                size_mb=round(size / (1024 * 1024), 2),
                url=item.url,
            )
        )

    return items, total_size, file_infos
