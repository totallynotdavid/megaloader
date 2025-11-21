import logging
import shutil
import tempfile

from pathlib import Path

import requests

from megaloader.item import DownloadItem

from api.config import DOWNLOAD_TIMEOUT


logger = logging.getLogger(__name__)


def create_temp_dir() -> Path:
    try:
        temp_dir = Path(tempfile.mkdtemp(prefix="megaloader_", dir="/tmp"))
        logger.info("Temp directory created", extra={"path": str(temp_dir)})
        return temp_dir
    except OSError:
        logger.error("Failed to create temp directory", exc_info=True)
        raise


def cleanup_temp(temp_dir: Path) -> None:
    try:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
            logger.debug("Temp directory cleaned", extra={"path": str(temp_dir)})
    except Exception:
        logger.error("Cleanup failed", exc_info=True)


def download_file(item: DownloadItem, output_dir: Path) -> Path | None:
    """
    Download single file with timeout and cleanup on failure.

    Returns file path on success, None on failure.
    """
    output_path = output_dir / item.filename

    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)

        logger.debug("Starting download", extra={"filename": item.filename})

        response = requests.get(
            item.download_url,
            stream=True,
            timeout=DOWNLOAD_TIMEOUT,
            headers=item.headers,
        )
        response.raise_for_status()

        bytes_downloaded = 0
        with output_path.open("wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    bytes_downloaded += len(chunk)

        logger.debug(
            "Download complete",
            extra={"filename": item.filename, "bytes": bytes_downloaded},
        )

        return output_path

    except Exception:
        logger.error(
            "Download failed", exc_info=True, extra={"filename": item.filename}
        )

        if output_path.exists():
            output_path.unlink()

        return None


def download_items(items: list[DownloadItem], temp_dir: Path) -> list[Path]:
    """
    Download all items to temp directory.

    Raises RuntimeError if no files downloaded successfully.
    """
    downloaded = []
    failed = []

    logger.info("Downloading items", extra={"count": len(items)})

    for item in items:
        file_path = download_file(item, temp_dir)

        if file_path:
            downloaded.append(file_path)
        else:
            failed.append(item.filename)

    if not downloaded:
        logger.error(
            "All downloads failed", extra={"total": len(items), "failed": len(failed)}
        )
        msg = "No files downloaded successfully"
        raise RuntimeError(msg)

    if failed:
        logger.warning(
            "Some downloads failed",
            extra={
                "successful": len(downloaded),
                "failed": len(failed),
                "failed_files": failed,
            },
        )

    logger.info(
        "Downloads complete",
        extra={"successful": len(downloaded), "failed": len(failed)},
    )

    return downloaded
