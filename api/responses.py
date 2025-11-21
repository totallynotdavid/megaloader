import logging
import zipfile

from io import BytesIO
from pathlib import Path

from fastapi.responses import Response


logger = logging.getLogger(__name__)

MIME_TYPES = {
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


def create_file_response(file_path: Path) -> Response:
    """
    Create download response for single file.

    Detects content type from extension.
    """
    if not file_path.exists():
        logger.error("File not found", extra={"path": str(file_path)})
        msg = f"File not found: {file_path}"
        raise FileNotFoundError(msg)

    try:
        content = file_path.read_bytes()
        content_type = MIME_TYPES.get(
            file_path.suffix.lower(), "application/octet-stream"
        )

        logger.info(
            "File response created",
            extra={
                "filename": file_path.name,
                "bytes": len(content),
                "type": content_type,
            },
        )

        return Response(
            content=content,
            media_type=content_type,
            headers={"Content-Disposition": f'attachment; filename="{file_path.name}"'},
        )

    except Exception:
        logger.error("Failed to create file response", exc_info=True)
        raise


def create_zip(files: list[Path], filename: str) -> Response:
    """
    Create ZIP archive response from multiple files.

    Skips missing files. Raises ValueError if no valid files.
    """
    if not files:
        msg = "No files provided"
        raise ValueError(msg)

    try:
        logger.debug("Creating ZIP", extra={"count": len(files), "name": filename})

        zip_buffer = BytesIO()
        files_added = 0

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for file_path in files:
                if file_path.exists():
                    zip_file.write(file_path, file_path.name)
                    files_added += 1
                else:
                    logger.warning("File missing", extra={"path": str(file_path)})

        if files_added == 0:
            msg = "No valid files to create ZIP"
            raise ValueError(msg)

        zip_buffer.seek(0)
        zip_content = zip_buffer.getvalue()

        logger.info(
            "ZIP created",
            extra={"files": files_added, "bytes": len(zip_content), "name": filename},
        )

        return Response(
            content=zip_content,
            media_type="application/zip",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    except Exception:
        logger.error("Failed to create ZIP", exc_info=True)
        raise
