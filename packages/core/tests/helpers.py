from collections.abc import Callable
from typing import Any

import pytest
import requests

from megaloader.item import DownloadItem
from megaloader.plugin import BasePlugin


# Validators


def validate_item_schema(item: DownloadItem) -> None:
    assert item.download_url.startswith(("http://", "https://")), (
        f"Invalid URL schema: {item.download_url}"
    )
    assert item.filename, "Filename cannot be empty"
    assert ".." not in item.filename, "Filename contains path traversal"
    assert "/" not in item.filename, "Filename contains directory separators"


def validate_is_video(item: DownloadItem) -> None:
    extensions = {".mp4", ".mkv", ".webm", ".mov", ".avi", ".m4v", ".ts"}
    assert any(item.filename.lower().endswith(ext) for ext in extensions), (
        f"Expected video extension, got: {item.filename}"
    )


def validate_is_image(item: DownloadItem) -> None:
    extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}
    assert any(item.filename.lower().endswith(ext) for ext in extensions), (
        f"Expected image extension, got: {item.filename}"
    )


def validate_has_size(item: DownloadItem) -> None:
    assert item.size_bytes is not None, "Item size_bytes is missing"
    assert item.size_bytes > 0, f"Item size must be positive, got {item.size_bytes}"


# Runners


def run_live_test(
    plugin_cls: type[BasePlugin],
    url: str,
    expected_min: int = 1,
    validator: Callable[[DownloadItem], None] | None = None,
    check_head: bool = False,
    **kwargs: Any,
) -> list[DownloadItem]:
    """
    Executes a plugin against a live URL and asserts validity.

    Flow:
    1. Initialize plugin
    2. Extract items
    3. Assert quantity
    4. Validate items
    """
    try:
        plugin = plugin_cls(url, **kwargs)
        items = list(plugin.extract())
    except requests.RequestException as e:
        # We skip on connection errors to avoid failing CI due to transient network issues
        pytest.skip(f"Network error connecting to {plugin_cls.__name__}: {e}")
        return []

    # 1. Quantity assertion
    assert len(items) >= expected_min, (
        f"Expected at least {expected_min} items from {url}, found {len(items)}"
    )

    # 2. Schema & custom validation
    for i, item in enumerate(items):
        try:
            validate_item_schema(item)
            if validator:
                validator(item)
        except AssertionError as e:
            pytest.fail(f"Validation failed on item #{i} ({item.filename}): {e}")

    # 3. Accessibility check (head request)
    if check_head and items:
        try:
            _assert_url_accessible(items[0].download_url)
        except AssertionError as e:
            pytest.fail(f"Downloadability check failed: {e}")

    return items


def _assert_url_accessible(url: str) -> None:
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

        resp = requests.head(url, timeout=10, allow_redirects=True, headers=headers)

        if resp.status_code == 405:
            resp = requests.get(url, timeout=10, stream=True, headers=headers)
            resp.close()

        assert resp.status_code < 400, f"HTTP {resp.status_code}"
    except requests.RequestException as e:
        msg = f"Connection failed: {e}"
        raise AssertionError(msg)
