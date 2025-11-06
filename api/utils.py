import logging

from urllib.parse import urlparse

import requests


logger = logging.getLogger(__name__)

# Constants
MAX_TOTAL_SIZE = 4 * 1024 * 1024
MAX_FILE_COUNT = 50
HEAD_REQUEST_TIMEOUT = 10


def format_size(size_bytes: float) -> str:
    """Format bytes as human-readable size."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


def extract_domain(url: str) -> str:
    """Extract domain from URL."""
    try:
        parsed = urlparse(url)
        return parsed.netloc.lower() if parsed.netloc else url.split("/")[0].lower()
    except Exception as e:  # noqa: BLE001
        logger.warning("Failed to parse domain: %s", e)
        return "unknown"


def get_file_size(url: str, headers: dict | None = None) -> int:
    """Get file size via HEAD request."""
    try:
        resp = requests.head(
            url, headers=headers, timeout=HEAD_REQUEST_TIMEOUT, allow_redirects=True
        )
        resp.raise_for_status()
        size = resp.headers.get("content-length")
        return int(size) if size else 0
    except Exception as e:  # noqa: BLE001
        logger.warning("Could not get size for %s: %s", url, e)
        return 0
