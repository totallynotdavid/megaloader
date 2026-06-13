from urllib.parse import urlsplit, urlunsplit

from megaloader.item import DownloadItem


def _strip_query(url: str) -> str:
    """
    Drop the query string from a URL for snapshotting.

    Plugins encode asset identity in the path; the query carries signed CDN
    params and per-request tokens that churn on every re-record. Stripping it
    keeps snapshots stable while still asserting the resolved asset.
    """
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))


def normalize_items(items: list[DownloadItem]) -> list[dict[str, object]]:
    """Render extracted items into a stable, snapshot-friendly shape."""
    return [
        {
            "download_url": _strip_query(item.download_url),
            "filename": item.filename,
            "collection_name": item.collection_name,
            "source_id": item.source_id,
            "headers": item.headers,
            "size_bytes": item.size_bytes,
        }
        for item in items
    ]
