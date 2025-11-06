import logging
import zipfile

from io import BytesIO
from pathlib import Path

from fastapi.responses import Response


logger = logging.getLogger(__name__)


def create_zip(files: list[Path], filename: str = "download.zip") -> Response:
    """Create ZIP response from files."""
    if not files:
        msg = "No files provided"
        raise ValueError(msg)

    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in files:
            if f.exists():
                zf.write(f, f.name)
            else:
                logger.warning("File missing: %s", f)

    zip_buffer.seek(0)
    return Response(
        content=zip_buffer.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def create_file_response(file_path: Path) -> Response:
    """Create response for single file."""
    if not file_path.exists():
        msg = f"File not found: {file_path}"
        raise FileNotFoundError(msg)

    content = file_path.read_bytes()
    ext_to_type = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".mp4": "video/mp4",
        ".webm": "video/webm",
        ".mp3": "audio/mpeg",
        ".wav": "audio/wav",
        ".pdf": "application/pdf",
    }
    content_type = ext_to_type.get(file_path.suffix.lower(), "application/octet-stream")

    return Response(
        content=content,
        media_type=content_type,
        headers={"Content-Disposition": f'attachment; filename="{file_path.name}"'},
    )
