"""Megaloader API - FastAPI routes."""

import logging

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from megaloader.plugins import get_plugin_class

from models import DownloadPreview, DownloadRequest, URLValidation, ValidationResult
from services import (
    cleanup_temp,
    create_file_response,
    create_temp_dir,
    create_zip,
    detect_plugin,
    download_items,
    format_size,
    get_items_info,
    MAX_TOTAL_SIZE,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# APP SETUP
# ============================================================================

app = FastAPI(
    title="Megaloader API",
    description="Download content from supported platforms (4MB limit)",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# ============================================================================
# ROUTES
# ============================================================================


@app.get("/")
async def root():
    """API info."""
    return {
        "status": "online",
        "service": "Megaloader API",
        "version": "2.0.0",
        "limits": {"max_size_mb": 4.0, "max_files": 50},
        "endpoints": {"validate": "POST /validate", "download": "POST /download"},
        "docs": "/docs"
    }


@app.post("/validate", response_model=ValidationResult)
async def validate_url(request: URLValidation) -> ValidationResult:
    """Validate if URL is supported."""
    url = request.url.strip()
    if not url:
        raise HTTPException(status_code=422, detail="URL cannot be empty")
    
    supported, plugin, domain = detect_plugin(url)
    return ValidationResult(supported=supported, domain=domain, plugin=plugin)


@app.post("/download")
async def download_content(request: DownloadRequest, bg: BackgroundTasks):
    """
    Download content from URL.
    - Size ≤ 4MB: Returns file(s)
    - Size > 4MB: Returns preview with file list
    """
    url = request.url.strip()
    
    # Validate & detect plugin
    supported, plugin_name, domain = detect_plugin(url)
    if not supported:
        raise HTTPException(status_code=400, detail=f"Unsupported domain: {domain}")
    
    plugin_class = get_plugin_class(url)
    if not plugin_class:
        raise HTTPException(status_code=400, detail="Failed to load plugin")
    
    # Get items and check size
    try:
        items, total_size, file_infos = get_items_info(plugin_class, url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Failed to get items info")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
    
    # Check if exceeds limit
    if total_size > MAX_TOTAL_SIZE:
        return DownloadPreview(
            total_size_bytes=total_size,
            total_size_mb=round(total_size / (1024 * 1024), 2),
            file_count=len(items),
            files=file_infos,
            exceeds_limit=True,
            message=f"Size {format_size(total_size)} exceeds 4MB limit. Download individually."
        )
    
    # Download files
    temp_dir = create_temp_dir()
    try:
        downloaded = download_items(items, plugin_class, url, temp_dir)
        logger.info(f"Downloaded {len(downloaded)} files")
        
        # Schedule cleanup
        bg.add_task(cleanup_temp, temp_dir)
        
        # Return response
        if len(downloaded) == 1:
            return create_file_response(downloaded[0])
        else:
            return create_zip(downloaded, f"{domain}_download.zip")
    
    except Exception as e:
        try:
            cleanup_temp(temp_dir)
        except Exception as ce:
            logger.error(f"Cleanup error: {ce}")
        logger.exception("Download failed")
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")

handler = app
