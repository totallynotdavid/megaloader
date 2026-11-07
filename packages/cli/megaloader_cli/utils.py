import logging
import re

from pathlib import Path

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


_WINDOWS_DEVICE_NAME = re.compile(r"(con|prn|aux|nul|com[1-9]|lpt[1-9])(\..*)?", re.I)


def sanitize_for_filesystem(name: str) -> str:
    """Make a name safe as a file or directory name on Windows and Unix.

    The result is never empty, never a dot segment, and never ends in a dot or
    space, so joining it to a directory cannot leave that directory.
    """
    sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name)
    sanitized = re.sub(r"_+", "_", sanitized)
    sanitized = sanitized.strip().strip("_").rstrip(". ")
    if not sanitized:
        return "unnamed"
    if _WINDOWS_DEVICE_NAME.fullmatch(sanitized):
        return f"_{sanitized}"
    return sanitized


def unclaimed_path(path: Path, claimed: set[Path]) -> Path:
    """Return path, or a numbered sibling when an earlier file already took it."""
    candidate = path
    number = 1
    while candidate in claimed:
        number += 1
        candidate = path.with_name(f"{path.stem} ({number}){path.suffix}")
    claimed.add(candidate)
    return candidate
