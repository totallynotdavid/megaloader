import logging
import shutil
import tempfile

from pathlib import Path

import requests

from megaloader.plugin import Item


logger = logging.getLogger(__name__)


def download_file(item: Item, output_dir: Path) -> bool:
    """Download a single item to output directory."""
    try:
        output_path = output_dir / item.filename
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Use referer from metadata if available
        headers = {}
        if item.meta and "referer" in item.meta:
            headers["Referer"] = item.meta["referer"]

        response = requests.get(item.url, stream=True, timeout=60, headers=headers)
        response.raise_for_status()

        with output_path.open("wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        logger.debug("Downloaded: %s", item.filename)
        return True
    except Exception:
        logger.exception("Download failed for %s", item.filename)
        if output_path.exists():
            output_path.unlink()
        return False


def download_items(
    items: list[Item], plugin_class: type, url: str, temp_dir: Path
) -> list[Path]:
    """Download all items to temp directory. Returns list of file paths."""
    downloaded = []

    for i, item in enumerate(items, 1):
        logger.debug("Downloading %d/%d: %s", i, len(items), item.filename)
        if download_file(item, temp_dir):
            file_path = temp_dir / item.filename
            if file_path.exists():
                downloaded.append(file_path)
            else:
                logger.warning("Success reported but file missing: %s", item.filename)
        else:
            logger.warning("Failed to download: %s", item.filename)

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
