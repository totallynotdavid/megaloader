import logging

import megaloader

from megaloader.item import DownloadItem
from megaloader.plugins import get_plugin_class

from api.config import ALLOWED_DOMAINS, MAX_FILE_COUNT
from api.models import FileInfo
from api.utils import get_file_size


logger = logging.getLogger(__name__)


def validate_url(domain: str) -> tuple[bool, str | None]:
    """
    Check if plugin exists for domain.

    Returns (supported, plugin_name).
    """
    try:
        plugin_class = get_plugin_class(domain)

        if plugin_class is None:
            return False, None

        is_allowed = domain in ALLOWED_DOMAINS
        plugin_name = plugin_class.__name__

        logger.debug(
            "URL validation complete",
            extra={"domain": domain, "plugin": plugin_name, "allowed": is_allowed},
        )

        return is_allowed, plugin_name

    except Exception:
        logger.error("Plugin detection failed", exc_info=True)
        return False, None


def extract_items(url: str, domain: str) -> list[DownloadItem]:
    """
    Extract items from URL with strict limits.

    Fails if count exceeds MAX_FILE_COUNT during extraction.
    Raises ValueError if no items found or count exceeded.
    """
    logger.debug("Starting extraction", extra={"domain": domain})

    items = []
    for item in megaloader.extract(url):
        items.append(item)

        if len(items) > MAX_FILE_COUNT:
            logger.warning(
                "File count exceeded during extraction",
                extra={"domain": domain, "count": len(items)},
            )
            msg = f"Too many files (>{MAX_FILE_COUNT})"
            raise ValueError(msg)

    if not items:
        logger.warning("No items extracted", extra={"domain": domain})
        msg = "No downloadable items found"
        raise ValueError(msg)

    logger.info("Extraction complete", extra={"domain": domain, "count": len(items)})

    return items


def get_items_with_sizes(items: list[DownloadItem]) -> tuple[int, list[FileInfo]]:
    """
    Calculate total size and create FileInfo list.

    Uses item headers for size checks. Files with undetermined sizes
    are included with 0 bytes.
    """
    total_size = 0
    file_infos = []

    logger.debug("Calculating sizes", extra={"count": len(items)})

    for item in items:
        size = get_file_size(item.download_url, item.headers)
        total_size += size

        file_infos.append(
            FileInfo(
                filename=item.filename,
                size_bytes=size,
                size_mb=round(size / (1024 * 1024), 2),
                url=item.download_url,
            )
        )

    logger.debug("Size calculation complete", extra={"total_bytes": total_size})

    return total_size, file_infos
