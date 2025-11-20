import logging
import re

from rich.console import Console
from rich.logging import RichHandler

# Shared console instance
console = Console()


def setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.WARNING

    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[
            RichHandler(
                console=console,
                rich_tracebacks=True,
                markup=True,
            )
        ],
    )


def sanitize_for_filesystem(name: str) -> str:
    """
    Sanitize a string to be safe for use as a filename or directory name.
    Removes/replaces characters that are invalid on Windows/Unix filesystems.

    Args:
        name: Input string (e.g., "Video: Title?")

    Returns:
        Safe string (e.g., "Video_ Title_")
    """
    # Replace invalid characters with underscore
    sanitized = re.sub(r'[<>:"/\\|?*]', "_", name)

    # Collapse multiple underscores
    sanitized = re.sub(r"_+", "_", sanitized)

    # Remove leading/trailing whitespace and underscores
    sanitized = sanitized.strip().strip("_")

    # Ensure not empty
    return sanitized if sanitized else "unnamed"
