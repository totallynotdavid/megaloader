import logging

from api.config import (
    CORS_ORIGINS,
    IS_PRODUCTION,
    MAX_FILE_COUNT,
    MAX_SIZE_BYTES,
    MAX_SIZE_MB,
    UNKNOWN_CLIENT,
    configure_logging,
)
from api.downloads import cleanup_temp, create_temp_dir, download_items
from api.extraction import extract_items, get_items_with_sizes, validate_url
from api.models import (
    DownloadPreview,
    DownloadRequest,
    URLValidation,
    ValidationResult,
)
from api.responses import create_file_response, create_zip
from api.security import check_rate_limit, validate_domain_whitelist
from api.utils import format_size
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from megaloader.exceptions import ExtractionError, UnsupportedDomainError


configure_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Megaloader API",
    description="Secure content extraction from whitelisted file hosting platforms",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)


@app.exception_handler(Exception)
def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(
        "Unhandled exception",
        extra={
            "client_ip": request.client.host
            if request.client is not None
            else UNKNOWN_CLIENT,
            "url": str(request.url),
            "method": request.method,
        },
    )

    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get("/")
async def root() -> dict:
    return {
        "status": "online",
        "service": "Megaloader API",
        "version": "2.0.0",
        "limits": {"max_size_mb": MAX_SIZE_MB, "max_files": MAX_FILE_COUNT},
        "endpoints": {"validate": "POST /validate", "download": "POST /download"},
        "docs": "/docs",
    }


@app.post("/validate", response_model=ValidationResult)
async def validate_endpoint(request: URLValidation, req: Request) -> ValidationResult:
    """
    Validate URL against whitelist and check plugin support.

    Security checks:
    1. Rate limiting
    2. Domain whitelist validation
    3. Plugin availability check
    """
    client_ip = req.client.host if req.client is not None else UNKNOWN_CLIENT

    await check_rate_limit(client_ip)

    url = request.url.strip()
    if not url:
        raise HTTPException(422, "URL required")

    domain = validate_domain_whitelist(url)

    supported, plugin = validate_url(domain)

    logger.info(
        "URL validated",
        extra={
            "client_ip": client_ip,
            "domain": domain,
            "supported": supported,
            "status_code": 200,
        },
    )

    return ValidationResult(supported=supported, domain=domain, plugin=plugin)


@app.post("/download", response_model=None)
async def download_endpoint(
    request: DownloadRequest, req: Request
) -> DownloadPreview | Response:
    """
    Extract and download content from whitelisted URL.

    Security checks:
    1. URL presence
    2. Domain whitelist
    3. Rate limiting
    4. File count limits during extraction
    5. Size limits before download

    Returns preview if size >4MB, otherwise downloads files.
    """
    client_ip = req.client.host if req.client is not None else UNKNOWN_CLIENT

    url = request.url.strip()
    if not url:
        raise HTTPException(422, "URL required")

    domain = validate_domain_whitelist(url)

    await check_rate_limit(client_ip)

    logger.info("Download request", extra={"client_ip": client_ip, "domain": domain})

    # Extract with count limits
    try:
        items = extract_items(url, domain)
    except UnsupportedDomainError as e:
        raise HTTPException(400, f"Domain '{e.domain}' not supported") from e
    except ValueError as e:
        raise HTTPException(422, str(e)) from e
    except ExtractionError as e:
        logger.exception(
            "Extraction failed",
            exc_info=not IS_PRODUCTION,
            extra={"client_ip": client_ip, "domain": domain},
        )
        raise HTTPException(500, "Extraction failed") from e

    # Get sizes with timeout
    try:
        total_size, file_infos = get_items_with_sizes(items)
    except Exception as e:
        logger.exception("Size calculation failed")
        raise HTTPException(500, "Unable to verify file sizes") from e

    # Return preview if exceeds limit
    if total_size > MAX_SIZE_BYTES:
        logger.info(
            "Size limit exceeded, returning preview",
            extra={
                "client_ip": client_ip,
                "domain": domain,
                "bytes": total_size,
                "status_code": 200,
            },
        )

        return DownloadPreview(
            total_size_bytes=total_size,
            total_size_mb=round(total_size / (1024 * 1024), 2),
            file_count=len(items),
            files=file_infos,
            exceeds_limit=True,
            limit_mb=MAX_SIZE_MB,
            message=f"Size {format_size(total_size)} exceeds {MAX_SIZE_MB}MB limit",
        )

    # Download files
    temp_dir = create_temp_dir()
    try:
        downloaded = download_items(items, temp_dir)

        logger.info(
            "Files downloaded",
            extra={"client_ip": client_ip, "domain": domain, "count": len(downloaded)},
        )

        if len(downloaded) == 1:
            return create_file_response(downloaded[0])

        return create_zip(downloaded, f"{domain}_download.zip")

    except Exception as e:
        logger.exception("Download failed")
        raise HTTPException(500, "Download failed") from e

    finally:
        cleanup_temp(temp_dir)
