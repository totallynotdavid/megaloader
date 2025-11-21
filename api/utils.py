import logging

import requests

from api.config import SIZE_CHECK_TIMEOUT


logger = logging.getLogger(__name__)


def format_size(size_bytes: int) -> str:
    """Format bytes to human-readable string (e.g., "1.50 MB")."""
    size_float = float(size_bytes)
    for unit in ["B", "KB", "MB", "GB"]:
        if size_float < 1024.0:
            return f"{size_float:.2f} {unit}"
        size_float /= 1024.0
    return f"{size_float:.2f} TB"


def get_file_size(url: str, headers: dict[str, str] | None = None) -> int:
    """
    Get file size via HEAD request with timeout.

    Returns 0 if size cannot be determined (timeout, error, missing header).
    """
    try:
        response = requests.head(
            url, headers=headers, timeout=SIZE_CHECK_TIMEOUT, allow_redirects=True
        )
        response.raise_for_status()

        content_length = response.headers.get("content-length")
        if not content_length:
            logger.debug("No content-length header", extra={"url": url})
            return 0

        size_bytes = int(content_length)
        logger.debug("Size retrieved", extra={"url": url, "bytes": size_bytes})
        return size_bytes

    except requests.exceptions.Timeout:
        logger.warning(
            "Size check timeout", extra={"url": url, "timeout": SIZE_CHECK_TIMEOUT}
        )
        return 0

    except requests.exceptions.HTTPError as e:
        logger.warning(
            "Size check HTTP error",
            extra={
                "url": url,
                "status": e.response.status_code if e.response else None,
            },
        )
        return 0

    except (ValueError, Exception) as e:  # noqa: BLE001 (catch-all makes sense here)
        logger.warning("Size check failed", extra={"url": url, "error": str(e)})
        return 0
