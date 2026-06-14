from pathlib import Path
from urllib.parse import unquote, urlparse


def filename_from_url(url: str, fallback: str = "") -> str:
    """
    Derive a leaf filename from a URL path, decoding percent-encoding.

    Returns the fallback when the path carries no usable name (for example a URL
    that ends in a slash). An empty fallback propagates the empty name to the
    caller, where DownloadItem rejects it.
    """
    return Path(unquote(urlparse(url).path)).name or fallback
