from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generator, Optional


@dataclass
class Item:
    """Represents a downloadable item exported by a plugin."""

    url: str
    filename: Optional[str] = None
    id: Optional[str] = None
    metadata: Optional[dict] = None


class BasePlugin(ABC):
    """
    Abstract base class for all MegaLoader plugins. Plugins must
    inherit from this class and implement the abstract methods.
    """

    def __init__(self, url: str, **kwargs):
        """
        Initializes the plugin with the main URL (e.g., album, post, list).

        Args:
            url (str): The URL to process.
            **kwargs: Additional configuration options for the plugin.
                      Subclasses should define and document their specific kwargs.
        """
        if not isinstance(url, str) or not url.strip():
            raise ValueError("URL must be a non-empty string.")
        self.url = url.strip()
        self._config = kwargs

    @abstractmethod
    def export(self) -> Generator[Item, None, None]:
        """
        Exports items (files) from the URL.

        Yields:
            Item: An Item object representing a downloadable file.
        """
        pass

    @abstractmethod
    def download_file(self, item: Item, output_dir: str) -> Optional[str]:
        """
        Downloads a single item to the specified output directory.

        Args:
            item (Item): The Item object representing the file to download.
            output_dir (str): The directory to save the file.

        Returns:
            The path to the downloaded file if successful, None otherwise.
        """
        pass
