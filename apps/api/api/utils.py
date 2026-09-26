import logging

import requests

from api.config import SIZE_CHECK_TIMEOUT
from api.safe_http import open_public_stream
from api.security import NonPublicURLError


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
        with open_public_stream(
            "HEAD", url, headers or {}, SIZE_CHECK_TIMEOUT
        ) as response:
            response.raise_for_status()
            content_length = response.headers.get("content-length")

    except NonPublicURLError as e:
        logger.warning("Size check refused", extra={"url": url, "error": str(e)})
        return 0

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
                "status": e.response.status_code if e.response is not None else None,
            },
        )
        return 0

    except requests.RequestException as e:
        logger.warning("Size check failed", extra={"url": url, "error": str(e)})
        return 0

    if not content_length:
        logger.debug("No content-length header", extra={"url": url})
        return 0

    try:
        size_bytes = int(content_length)
    except ValueError:
        logger.warning("Invalid content-length", extra={"url": url})
        return 0

    if size_bytes < 0:
        logger.warning("Negative content-length", extra={"url": url})
        return 0

    logger.debug("Size retrieved", extra={"url": url, "bytes": size_bytes})
    return size_bytes
