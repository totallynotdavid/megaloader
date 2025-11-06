"""All business logic and utilities for Megaloader API."""

import logging
import shutil
import tempfile
import zipfile
from io import BytesIO
from pathlib import Path
from urllib.parse import urlparse

import requests
from fastapi.responses import Response
from megaloader.plugin import Item
from megaloader.plugins import get_plugin_class

from models import FileInfo

logger = logging.getLogger(__name__)

# ============================================================================
# CONSTANTS
# ============================================================================

MAX_TOTAL_SIZE = 4 * 1024 * 1024
MAX_FILE_COUNT = 50
HEAD_REQUEST_TIMEOUT = 10


# ============================================================================
# UTILITIES
# ============================================================================

def format_size(size_bytes: int) -> str:
    """Format bytes as human-readable size."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


def extract_domain(url: str) -> str:
    """Extract domain from URL."""
    try:
        parsed = urlparse(url)
        return parsed.netloc.lower() if parsed.netloc else url.split("/")[0].lower()
    except Exception as e:
        logger.warning(f"Failed to parse domain: {e}")
        return "unknown"


def get_file_size(url: str, headers: dict | None = None) -> int:
    """Get file size via HEAD request."""
    try:
        resp = requests.head(url, headers=headers, timeout=HEAD_REQUEST_TIMEOUT, allow_redirects=True)
        resp.raise_for_status()
        size = resp.headers.get("content-length")
        return int(size) if size else 0
    except Exception as e:
        logger.warning(f"Could not get size for {url}: {e}")
        return 0


# ============================================================================
# PLUGIN DETECTION
# ============================================================================

def detect_plugin(url: str) -> tuple[bool, str | None, str]:
    """Detect if URL is supported. Returns (is_supported, plugin_name, domain)."""
    domain = extract_domain(url)
    try:
        plugin_class = get_plugin_class(url)
        return (True, plugin_class.__name__, domain) if plugin_class else (False, None, domain)
    except Exception as e:
        logger.error(f"Plugin detection failed: {e}")
        return False, None, domain


def get_items_info(plugin_class: type, url: str) -> tuple[list[Item], int, list[FileInfo]]:
    """Get items from plugin and calculate total size."""
    plugin = plugin_class(url)
    items = list(plugin.export())
    
    if not items:
        raise ValueError("No downloadable items found")
    if len(items) > MAX_FILE_COUNT:
        raise ValueError(f"Too many files ({len(items)}). Maximum is {MAX_FILE_COUNT}")
    
    logger.info(f"Found {len(items)} items")
    
    total_size = 0
    file_infos = []
    
    for item in items:
        headers = None
        if hasattr(item, 'metadata') and item.metadata and 'referer' in item.metadata:
            headers = {'Referer': item.metadata['referer']}
        
        size = get_file_size(item.url, headers)
        total_size += size
        file_infos.append(FileInfo(
            filename=item.filename,
            size_bytes=size,
            size_mb=round(size / (1024 * 1024), 2),
            url=item.url
        ))
    
    return items, total_size, file_infos


# ============================================================================
# DOWNLOADS & FILE OPERATIONS
# ============================================================================

def download_items(items: list[Item], plugin_class: type, url: str, temp_dir: Path) -> list[Path]:
    """Download all items to temp directory. Returns list of file paths."""
    plugin = plugin_class(url)
    downloaded = []
    
    for i, item in enumerate(items, 1):
        try:
            logger.debug(f"Downloading {i}/{len(items)}: {item.filename}")
            if plugin.download_file(item, str(temp_dir)):
                file_path = temp_dir / item.filename
                if file_path.exists():
                    downloaded.append(file_path)
                else:
                    logger.warning(f"Success reported but file missing: {item.filename}")
            else:
                logger.warning(f"Failed to download: {item.filename}")
        except Exception as e:
            logger.error(f"Error downloading {item.filename}: {e}")
    
    if not downloaded:
        raise RuntimeError("No files downloaded successfully")
    return downloaded


def cleanup_temp(temp_dir: Path) -> None:
    """Clean up temporary directory."""
    try:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
            logger.debug(f"Cleaned up: {temp_dir}")
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        raise


def create_zip(files: list[Path], filename: str = "download.zip") -> Response:
    """Create ZIP response from files."""
    if not files:
        raise ValueError("No files provided")
    
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        for f in files:
            if f.exists():
                zf.write(f, f.name)
            else:
                logger.warning(f"File missing: {f}")
    
    zip_buffer.seek(0)
    return Response(
        content=zip_buffer.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


def create_file_response(file_path: Path) -> Response:
    """Create response for single file."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    content = file_path.read_bytes()
    ext_to_type = {
        '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png',
        '.gif': 'image/gif', '.mp4': 'video/mp4', '.webm': 'video/webm',
        '.mp3': 'audio/mpeg', '.wav': 'audio/wav', '.pdf': 'application/pdf',
    }
    content_type = ext_to_type.get(file_path.suffix.lower(), "application/octet-stream")
    
    return Response(
        content=content,
        media_type=content_type,
        headers={"Content-Disposition": f'attachment; filename="{file_path.name}"'}
    )


def create_temp_dir() -> Path:
    """Create temporary directory."""
    temp_dir = Path(tempfile.mkdtemp(prefix="megaloader_"))
    logger.info(f"Created temp: {temp_dir}")
    return temp_dir
