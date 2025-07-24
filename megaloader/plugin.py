from abc import ABC, abstractmethod
from collections.abc import Generator
from dataclasses import dataclass
from typing import Optional


@dataclass
class Item:
    """Represents a downloadable item."""

    url: str
    filename: str
    file_id: Optional[str] = None
    metadata: Optional[dict] = None


class BasePlugin(ABC):
    """
    Base class for all megaloader plugins.

    Plugins handle extraction and downloading of files from specific hosting services.
    Each plugin is responsible for parsing the service's pages and generating download URLs.
    """

    def __init__(self, url: str, **kwargs):
        if not isinstance(url, str) or not url.strip():
            raise ValueError("URL must be a non-empty string")
        self.url = url.strip()
        self._config = kwargs

    @abstractmethod
    def export(self) -> Generator[Item, None, None]:
        """
        Extract downloadable items from the URL.

        Yields:
            Item: Each downloadable file found at the URL
        """

    @abstractmethod
    def download_file(self, item: Item, output_dir: str) -> bool:
        """
        Download a single item to the specified directory.

        Args:
            item: The item to download (from export())
            output_dir: Directory to save the file to

        Returns:
            True if download succeeded, False otherwise
        """
