import logging
import re

from rich.console import Console
from rich.logging import RichHandler


# Shared console instance to prevent print interleaving
console = Console()

INVALID_DIR_CHARS = r'[<>:"/\\|?*]'


def setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=console, rich_tracebacks=True, markup=True)],
    )


def sanitize_filename(name: str) -> str:
    """
    Sanitize a string to be safe for use as a filename.

    Args:
        name: The input string (e.g., "Video: Title?")

    Returns:
        Safe string (e.g., "Video_ Title_")
    """
    # Replace invalid chars with underscore
    clean = re.sub(INVALID_DIR_CHARS, "_", name)
    # Collapse multiple underscores
    clean = re.sub(r"_+", "_", clean)
    return clean.strip()
