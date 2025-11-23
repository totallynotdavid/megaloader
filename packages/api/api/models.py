from pydantic import BaseModel, Field


class URLValidation(BaseModel):
    url: str = Field(..., min_length=1, max_length=2048)


class ValidationResult(BaseModel):
    supported: bool
    domain: str
    plugin: str | None


class DownloadRequest(BaseModel):
    url: str = Field(..., min_length=1, max_length=2048)


class FileInfo(BaseModel):
    """Individual file metadata."""

    filename: str
    size_bytes: int = Field(..., ge=0)
    size_mb: float = Field(..., ge=0.0)
    url: str


class DownloadPreview(BaseModel):
    """Preview when content exceeds size limit."""

    total_size_bytes: int = Field(..., ge=0)
    total_size_mb: float = Field(..., ge=0.0)
    file_count: int = Field(..., ge=0)
    files: list[FileInfo]
    exceeds_limit: bool = True
    limit_mb: float
    message: str
