from dataclasses import dataclass, field


@dataclass
class DownloadItem:
    """
    Represents a single downloadable file with metadata.

    Attributes:
        download_url: Direct URL to download the file
        filename: Original filename (may need sanitization for filesystem)
        collection_name: Optional grouping (album/gallery/user)
        source_id: Optional unique identifier from the source platform
        headers: Optional HTTP headers required for download (e.g., Referer)
        size_bytes: Optional file size in bytes
    """

    download_url: str
    filename: str
    collection_name: str | None = None
    source_id: str | None = None
    headers: dict[str, str] = field(default_factory=dict)
    size_bytes: int | None = None

    def __post_init__(self) -> None:
        """Validate required fields."""
        if not self.download_url:
            msg = "download_url cannot be empty"
            raise ValueError(msg)
        if not self.filename:
            msg = "filename cannot be empty"
            raise ValueError(msg)
