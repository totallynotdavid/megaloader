import os
import shutil
import requests
from urllib.parse import unquote, urlparse, urljoin


def __build_headers(url: str, custom_headers: dict = None, as_list: bool = False):
    """
    Builds a standard set of HTTP headers for requests.

    Args:
        url (str): The target URL for the request.
        custom_headers (dict, optional): Additional headers to merge in.
        as_list (bool, optional): If True, returns headers as a list of tuples.
                                  Defaults to False (returns a dict).

    Returns:
        dict | list: The constructed headers.
    """
    parsed_url = urlparse(url)  # Get the base origin from the URL
    origin = f"{parsed_url.scheme}://{parsed_url.netloc}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:95.0) Gecko/20100101 Firefox/95.0",
        "Accept": "*/*",
        "Referer": urljoin(origin, "/"),  # Ensures a trailing slash
        "Origin": origin,
        "Connection": "keep-alive",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
    }
    if custom_headers:
        # Ensure keys and values are strings
        for k, v in custom_headers.items():
            headers[str(k)] = str(v)
    if as_list:
        return list(headers.items())
    return headers


def http_download(
    url: str, output_folder: str, custom_headers: dict = None, headers_required=True
):
    """
    Downloads a file from a URL to a specified folder.

    Args:
        url (str): The URL of the file to download.
        output_folder (str): The directory to save the file in.
        custom_headers (dict, optional): Custom headers to add to the request.
        headers_required (bool, optional): Whether to add default headers.
                                           Defaults to True.
    """
    # Decode URL to handle percent-encoded characters in the filename
    url = unquote(url)
    # Extract filename from URL path, ignoring query parameters
    filename = os.path.basename(urlparse(url).path)
    # Sanitize filename: replace %20 with space (already unquoted) and handle potential issues
    filename = filename.replace("%20", " ").strip()

    if not filename:
        print(f"[WARNING] Could not determine filename from URL: {url}. Skipping.")
        return

    output_path = os.path.join(os.path.abspath(output_folder), filename)

    if os.path.exists(output_path):
        print(f"[INFO] File already exists, skipping: {output_path}")
        return

    os.makedirs(output_folder, exist_ok=True)

    headers = None
    if headers_required:
        headers = __build_headers(url, custom_headers)

    try:
        with requests.get(url, headers=headers, stream=True, timeout=30) as response:
            if response.status_code in (403, 404, 405, 500, 502, 503, 504):
                print(
                    f"[ERROR] Failed to download {url}. Status code: {response.status_code}"
                )
                return
            response.raise_for_status()  # Raise for other HTTP errors (4xx, 5xx)

            with open(output_path, "wb") as output_file:
                shutil.copyfileobj(response.raw, output_file)
        print(f"[INFO] Downloaded: {filename} -> {output_path}")
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Network error during download of {url}: {e}")
        if os.path.exists(output_path):
            try:
                os.remove(output_path)
            except OSError:
                pass
    except OSError as e:
        print(f"[ERROR] File system error saving {filename} to {output_folder}: {e}")
        if os.path.exists(output_path):
            try:
                os.remove(output_path)
            except OSError:
                pass
