from abc import ABC, abstractmethod
from typing import Generator, Any, Optional


class BasePlugin(ABC):
    """
    Abstract base class for all MegaLoader plugins. Plugins must
    inherit from this class and implement the abstract methods.
    """

    def __init__(self, url: str):
        """
        Initializes the plugin with the main URL (e.g., album, post, list).
        """
        if not isinstance(url, str) or not url.strip():
            raise ValueError("URL must be a non-empty string.")
        self.url = url.strip()

    @abstractmethod
    def export(self) -> Generator[Any, None, None]:
        """
        Abstract method to export downloadable item identifiers.

        This method should yield items that can be passed to `download_file`.
        The specific type yielded (e.g., str, tuple) depends on the plugin's
        `download_file` implementation.

        Yields:
            Generator[Any, None, None]: An iterable of items representing
                                        downloadable resources. Often strings (URLs),
                                        but can be tuples or other data structures
                                        needed by `download_file`.
        """
        pass

    @abstractmethod
    def download_file(self, item: Any, output_dir: str) -> Optional[Any]:
        """
        Abstract method to download a single file.

        The `item` argument is what `export` yields for this specific plugin.
        For simple URL exports, it's often `download_file(self, file_url: str, output_dir: str)`.
        For more complex exports (like Pixeldrain), it might be
        `download_file(self, item: Tuple[str, str], output_dir: str)`.

        Args:
            item (Any): The item representing the resource to download, as yielded by `export`.
            output_dir (str): The directory where the file should be saved.

        Returns:
            Optional[Any]: Plugin-specific indicator of success/failure.
                           Often the path to the downloaded file on success, None/False otherwise.
        """
        pass
