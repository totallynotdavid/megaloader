import logging
import shutil
import tempfile

from pathlib import Path

import requests

from megaloader.item import DownloadItem

from api.config import DOWNLOAD_TIMEOUT, MAX_SIZE_BYTES
from api.safe_http import open_public_stream
from api.security import NonPublicURLError


logger = logging.getLogger(__name__)


class SizeLimitExceededError(Exception):
    """A response body grew past the size budget while streaming."""


class UnsafeFilenameError(ValueError):
    """An upstream filename that cannot be written safely inside the temp dir."""


def safe_basename(filename: str) -> str:
    """
    Reduce an upstream filename to a leaf name for the temp dir.

    Both separator styles count as separators, whatever the host OS. Absolute
    paths, empty names, dot segments and NUL bytes are refused, so a write can
    never land outside the directory it is joined to.
    """
    if filename.startswith(("/", "\\")) or "\0" in filename:
        msg = "Filename is an absolute path or contains NUL"
        raise UnsafeFilenameError(msg)

    name = filename.replace("\\", "/").rsplit("/", 1)[-1]
    if name in ("", ".", ".."):
        msg = f"Filename has no usable leaf name: {filename!r}"
        raise UnsafeFilenameError(msg)

    return name


def create_temp_dir() -> Path:
    try:
        temp_dir = Path(tempfile.mkdtemp(prefix="megaloader_", dir="/tmp"))
        logger.info("Temp directory created", extra={"path": str(temp_dir)})
        return temp_dir
    except OSError:
        logger.exception("Failed to create temp directory")
        raise


def cleanup_temp(temp_dir: Path) -> None:
    try:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
            logger.debug("Temp directory cleaned", extra={"path": str(temp_dir)})
    except OSError:
        logger.exception("Cleanup failed")


def write_within_budget(response: requests.Response, path: Path, budget: int) -> int:
    """
    Stream the body to path and return the bytes written.

    Content-Length is advisory (hosts omit or understate it), so the limit is
    enforced here on the decoded bytes. Raises SizeLimitExceededError as soon as
    the body passes budget, before writing the chunk that crosses it.
    """
    written = 0
    with path.open("wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            written += len(chunk)
            if written > budget:
                raise SizeLimitExceededError
            f.write(chunk)
    return written


def download_file(item: DownloadItem, output_dir: Path, budget: int) -> Path | None:
    """
    Download single file with timeout and cleanup on failure.

    Returns file path on success, None on failure. Raises SizeLimitExceededError
    if the body is larger than budget bytes.
    """
    try:
        output_path = output_dir / safe_basename(item.filename)
    except UnsafeFilenameError:
        logger.warning("Unsafe filename refused", extra={"file_name": item.filename})
        return None

    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)

        logger.debug("Starting download", extra={"file_name": item.filename})

        headers = item.headers.copy()
        if "User-Agent" not in headers:
            headers["User-Agent"] = (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )

        with open_public_stream(
            "GET", item.download_url, headers, DOWNLOAD_TIMEOUT
        ) as response:
            response.raise_for_status()
            bytes_downloaded = write_within_budget(response, output_path, budget)

        logger.debug(
            "Download complete",
            extra={"file_name": item.filename, "bytes": bytes_downloaded},
        )

        return output_path

    except (NonPublicURLError, requests.RequestException, OSError):
        logger.exception("Download failed", extra={"file_name": item.filename})
        output_path.unlink(missing_ok=True)
        return None

    except SizeLimitExceededError:
        output_path.unlink(missing_ok=True)
        raise


def download_items(items: list[DownloadItem], temp_dir: Path) -> list[Path]:
    """
    Download all items to temp directory, within one size budget for the request.

    Raises SizeLimitExceededError if the files together pass MAX_SIZE_BYTES and
    RuntimeError if no files downloaded successfully.
    """
    downloaded: list[Path] = []
    failed = []
    remaining = MAX_SIZE_BYTES

    logger.info("Downloading items", extra={"count": len(items)})

    for item in items:
        file_path = download_file(item, temp_dir, remaining)

        if file_path:
            downloaded.append(file_path)
            remaining -= file_path.stat().st_size
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
