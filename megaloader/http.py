import contextlib
import logging
import os

from typing import Optional
from urllib.parse import unquote, urlparse

import requests


logger = logging.getLogger(__name__)

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Connection": "keep-alive",
}


def download_file(
    url: str,
    output_dir: str,
    filename: Optional[str] = None,
    headers: Optional[dict[str, str]] = None,
    timeout: int = 30,
) -> Optional[str]:
    """
    Download a file from URL to output directory.

    Args:
        url: Direct download URL
        output_dir: Directory to save file to
        filename: Custom filename (extracted from URL if None)
        headers: Additional HTTP headers
        timeout: Request timeout in seconds

    Returns:
        Path to downloaded file, or None if failed
    """
    if filename is None:
        filename = os.path.basename(unquote(urlparse(url).path))
        if not filename:
            logger.error(f"Could not determine filename from URL: {url}")
            return None

    # Sanitize filename
    filename = filename.strip().replace("/", "_").replace("\\", "_")
    output_path = os.path.join(os.path.abspath(output_dir), filename)

    if os.path.exists(output_path):
        logger.info(f"File already exists: {filename}")
        return output_path

    os.makedirs(output_dir, exist_ok=True)

    req_headers = DEFAULT_HEADERS.copy()
    if headers:
        req_headers.update(headers)

    try:
        logger.debug(f"Downloading: {url}")
        with requests.get(
            url, headers=req_headers, stream=True, timeout=timeout
        ) as response:
            response.raise_for_status()

            with open(output_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

        logger.debug(f"Downloaded: {filename}")
        return output_path

    except requests.RequestException as e:
        logger.error(f"Download failed for {filename}: {e}")
        if os.path.exists(output_path):
            with contextlib.suppress(OSError):
                os.remove(output_path)
        return None
