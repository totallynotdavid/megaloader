from megaloader.item import DownloadItem


def assert_valid_item(item: DownloadItem) -> None:
    """Validate that a DownloadItem has valid URL and filename."""
    assert item.download_url.startswith(("http://", "https://")), (
        f"Invalid URL schema: {item.download_url}"
    )
    assert item.filename, "Filename cannot be empty"
    assert ".." not in item.filename, "Filename contains path traversal"
    assert "/" not in item.filename, "Filename contains directory separators"
