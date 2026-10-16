"""Megaloader: find the downloadable files behind a hosting-site link."""

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
