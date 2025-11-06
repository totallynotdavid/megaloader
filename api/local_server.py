from pathlib import Path
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from megaloader import download
from megaloader.exceptions import MegaloaderError
from megaloader.plugins import get_plugin_class
from pydantic import BaseModel


app = FastAPI(
    title="Megaloader API",
    description="API for downloading content from various platforms",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],  # VitePress dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create downloads directory
DOWNLOAD_DIR = Path(__file__).parent / "downloads"
DOWNLOAD_DIR.mkdir(exist_ok=True)


class DownloadRequest(BaseModel):
    url: str


class ValidationResponse(BaseModel):
    supported: bool
    plugin: str | None = None
    domain: str


class DownloadResponse(BaseModel):
    success: bool
    message: str | None = None
    error: str | None = None
    plugin: str | None = None


@app.get("/api/validate-url")
async def validate_url(url: str = Query(..., description="URL to validate")):
    try:
        if not url:
            raise HTTPException(status_code=400, detail="Missing url parameter")

        # Extract domain from URL
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            if not domain:
                domain = url.split("/")[0] if "/" in url else url
        except:
            raise HTTPException(status_code=400, detail="Invalid URL format")

        # Check if supported using actual megaloader plugin detection
        try:
            plugin_class = get_plugin_class(url)
            if plugin_class:
                return ValidationResponse(
                    supported=True, plugin=plugin_class.__name__, domain=domain
                )
        except:
            pass

        return ValidationResponse(supported=False, domain=domain)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {e!s}")


@app.post("/api/download")
async def download_content(request: DownloadRequest):
    try:
        url = request.url.strip()
        if not url:
            raise HTTPException(status_code=400, detail="URL is required")

        # Detect plugin
        plugin_class = get_plugin_class(url)
        if not plugin_class:
            raise HTTPException(status_code=400, detail="No plugin found for this URL")

        # Download
        success = download(
            url,
            str(DOWNLOAD_DIR),
            plugin_class=plugin_class,
            use_proxy=False,  # Default to no proxy for demo
            create_album_subdirs=True,
        )

        if success:
            return DownloadResponse(
                success=True,
                message=f"Successfully downloaded from {url}",
                plugin=plugin_class.__name__,
            )
        raise HTTPException(status_code=500, detail="Download failed")

    except MegaloaderError as e:
        raise HTTPException(status_code=400, detail=f"Download error: {e!s}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e!s}")


@app.get("/")
async def root():
    return {"message": "Megaloader API is running!", "docs": "/docs"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
