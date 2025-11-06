"""Pydantic models for Megaloader API."""

from pydantic import BaseModel, Field


class URLValidation(BaseModel):
    url: str = Field(..., min_length=1)


class ValidationResult(BaseModel):
    supported: bool
    domain: str
    plugin: str | None = None


class DownloadRequest(BaseModel):
    url: str = Field(..., min_length=1)


class FileInfo(BaseModel):
    filename: str
    size_bytes: int
    size_mb: float
    url: str


class DownloadPreview(BaseModel):
    total_size_bytes: int
    total_size_mb: float
    file_count: int
    files: list[FileInfo]
    exceeds_limit: bool
    limit_mb: float = 4.0
    message: str
