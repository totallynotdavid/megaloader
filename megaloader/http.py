import os
import logging
import requests
from urllib.parse import unquote, urlparse, urljoin
from typing import Optional, Dict, Any
from .exceptions import DownloadError

logger = logging.getLogger(__name__)

# Default headers, can be overridden
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:95.0) Gecko/20100101 Firefox/95.0",
    "Accept": "*/*",
    "Referer": "",
    "Origin": "",
    "Connection": "keep-alive",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
    "Pragma": "no-cache",
    "Cache-Control": "no-cache",
}


def __build_headers(
    url: str, custom_headers: Optional[Dict[str, Any]] = None
) -> Dict[str, str]:
    parsed_url = urlparse(url)
    origin = f"{parsed_url.scheme}://{parsed_url.netloc}"

    headers = DEFAULT_HEADERS.copy()
    headers["Referer"] = urljoin(origin, "/")
    headers["Origin"] = origin

    if custom_headers:
        # Ensure keys and values are strings
        for k, v in custom_headers.items():
            headers[str(k)] = str(v)
    return headers


def http_download(
    url: str,
    output_folder: str,
    custom_headers: Optional[Dict[str, Any]] = None,
    headers_required: bool = True,
    session: Optional[requests.Session] = None,
    chunk_size: int = 8192,
    timeout: int = 30,
) -> Optional[str]:
    """
    Downloads a file from a URL to a specified folder.

    Args:
        url (str): The URL of the file to download.
        output_folder (str): The directory to save the file.
        custom_headers (dict): Optional dictionary of headers to add/override.
        headers_required (bool): Whether to use default headers.
        session (obj): An optional requests.Session object to use.
        chunk_size (int): Size of chunks to read/write.
        timeout (int): Request timeout in seconds.

    Returns:
        The absolute path to the downloaded file if successful, None otherwise.

    Raises:
        DownloadError: For errors during the download process (network, file system).
        requests.exceptions.RequestException: For network-related errors from requests.
        OSError: For file system related errors.
    """
    # Decode URL to handle percent-encoded characters in the filename
    url = unquote(url)
    # Extract filename from URL path, ignoring query parameters
    filename = os.path.basename(urlparse(url).path)
    # Sanitize filename: replace %20 with space (already unquoted) and handle potential issues
    filename = filename.replace("%20", " ").strip()

    if not filename:
        logger.warning(f"Could not determine filename from URL: {url}. Skipping.")
        return None

    output_path = os.path.join(os.path.abspath(output_folder), filename)

    if os.path.exists(output_path):
        logger.info(f"File already exists, skipping: {output_path}")
        return output_path

    os.makedirs(output_folder, exist_ok=True)

    headers = None
    if headers_required:
        headers = __build_headers(url, custom_headers)

    req_session = session if session is not None else requests.Session()

    try:
        logger.debug(f"Starting download: {url}")
        with req_session.get(
            url, headers=headers, stream=True, timeout=timeout
        ) as response:
            if response.status_code in (403, 404, 405, 500, 502, 503, 504):
                error_msg = (
                    f"Failed to download {url}. Status code: {response.status_code}"
                )
                logger.error(error_msg)
                raise DownloadError(error_msg)
            response.raise_for_status()  # Raise for other HTTP errors (4xx, 5xx)
            logger.debug(f"Download request successful, writing to file: {output_path}")
            with open(output_path, "wb") as output_file:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:  # Filter out keep-alive chunks
                        output_file.write(chunk)
        logger.info(f"Downloaded: {filename} -> {output_path}")
        return output_path
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error during download of {url}: {e}")
        # Attempt cleanup on network error
        if os.path.exists(output_path):
            try:
                os.remove(output_path)
                logger.debug(f"Removed incomplete file: {output_path}")
            except OSError as remove_error:
                logger.warning(
                    f"Failed to remove incomplete file {output_path}: {remove_error}"
                )
        raise DownloadError(f"Network error during download: {e}") from e
    except OSError as e:
        logger.error(f"File system error saving {filename} to {output_folder}: {e}")
        # Attempt cleanup on file system error
        if os.path.exists(output_path):
            try:
                os.remove(output_path)
                logger.debug(f"Removed incomplete file: {output_path}")
            except OSError as remove_error:
                logger.warning(
                    f"Failed to remove incomplete file {output_path}: {remove_error}"
                )
        raise DownloadError(f"File system error during download: {e}") from e
