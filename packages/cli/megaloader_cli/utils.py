import logging
import re

from rich.console import Console
from rich.logging import RichHandler


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
    """Make a name safe as a file or directory name on Windows and Unix."""
    sanitized = re.sub(r'[<>:"/\\|?*]', "_", name)
    sanitized = re.sub(r"_+", "_", sanitized)
    sanitized = sanitized.strip().strip("_")
    return sanitized or "unnamed"
