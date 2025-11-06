import logging
import shutil
import tempfile

from pathlib import Path

from megaloader.plugin import Item


logger = logging.getLogger(__name__)


def download_items(
    items: list[Item], plugin_class: type, url: str, temp_dir: Path
) -> list[Path]:
    """Download all items to temp directory. Returns list of file paths."""
    plugin = plugin_class(url)
    downloaded = []

    for i, item in enumerate(items, 1):
        try:
            logger.debug("Downloading %d/%d: %s", i, len(items), item.filename)
            if plugin.download_file(item, str(temp_dir)):
                file_path = temp_dir / item.filename
                if file_path.exists():
                    downloaded.append(file_path)
                else:
                    logger.warning(
                        "Success reported but file missing: %s", item.filename
                    )
            else:
                logger.warning("Failed to download: %s", item.filename)
        except Exception:
            logger.exception("Error downloading %s", item.filename)

    if not downloaded:
        msg = "No files downloaded successfully"
        raise RuntimeError(msg)
    return downloaded


def cleanup_temp(temp_dir: Path) -> None:
    try:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
            logger.debug("Cleaned up: %s", temp_dir)
    except Exception:
        logger.exception("Cleanup failed")
        raise


def create_temp_dir() -> Path:
    temp_dir = Path(tempfile.mkdtemp(prefix="megaloader_"))
    logger.info("Created temp: %s", temp_dir)
    return temp_dir
