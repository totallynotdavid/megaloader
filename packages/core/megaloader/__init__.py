"""
Megaloader - Extract downloadable content metadata from file hosting platforms.

Basic usage:
    import megaloader as mgl

    for item in mgl.extract(url):
        print(item.url, item.filename)

    # With plugin-specific options
    items = mgl.extract(url, password="secret")
    items = mgl.extract(url, session_id="cookie_value")
"""

from megaloader._version import __version__
from megaloader.api import extract
from megaloader.exceptions import ExtractionError, UnsupportedDomainError
from megaloader.item import DownloadItem


__all__ = [
    "DownloadItem",
    "ExtractionError",
    "UnsupportedDomainError",
    "__version__",
    "extract",
]
