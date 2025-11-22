---
title: Creating plugins
description: Guide to building custom plugins for new platforms
outline: [2, 4]
prev:
  text: "Plugin options"
  link: "/plugins/options"
next:
  text: "Contributing"
  link: "/development/contributing"
---

# Creating plugins

This guide walks through creating a plugin for a new platform. You'll understand
the architecture and be able to add support for any file hosting platform.

## Plugin architecture

Every plugin:

1. Inherits from `BasePlugin` for session management and retry logic
2. Implements `extract()` to yield `DownloadItem` objects
3. Optionally overrides `_configure_session()` for platform-specific headers
4. Gets registered in `PLUGIN_REGISTRY` to map domains to the plugin

## Minimal example

The simplest possible plugin:

```python
from collections.abc import Generator
from megaloader.item import DownloadItem
from megaloader.plugin import BasePlugin

class SimpleHost(BasePlugin):
    def extract(self) -> Generator[DownloadItem, None, None]:
        response = self.session.get(self.url, timeout=30)
        response.raise_for_status()

        data = response.json()

        for file_data in data["files"]:
            yield DownloadItem(
                download_url=file_data["url"],
                filename=file_data["name"],
                size_bytes=file_data.get("size"),
            )
```

That's it. `BasePlugin` handles session creation, retry logic, and default
headers automatically.

## BasePlugin reference

**Provided attributes:**

- `self.url` - The URL passed to `extract()`
- `self.options` - Dictionary of keyword arguments
- `self.session` - Lazy-loaded `requests.Session` with retry logic

**Provided methods:**

- `_create_session()` - Creates session with retry strategy (don't override)
- `_configure_session(session)` - Override to add custom headers/cookies

**Required implementation:**

- `extract()` - Must yield `DownloadItem` objects

## Building a real plugin

Let's build a plugin for a fictional platform "FileBox" with:

- Album URLs: `https://filebox.com/album/abc123`
- File URLs: `https://filebox.com/file/xyz789`
- JSON API at `https://api.filebox.com/v1/`

### Create the plugin class

```python
import logging
import re
from collections.abc import Generator
from typing import Any

from megaloader.item import DownloadItem
from megaloader.plugin import BasePlugin

logger = logging.getLogger(__name__)

class FileBox(BasePlugin):
    API_BASE = "https://api.filebox.com/v1"

    def __init__(self, url: str, **options: Any) -> None:
        super().__init__(url, **options)
        self.content_type, self.content_id = self._parse_url(url)

    def _parse_url(self, url: str) -> tuple[str, str]:
        if match := re.search(r"filebox\.com/(album|file)/([\w-]+)", url):
            return match.group(1), match.group(2)

        raise ValueError(f"Invalid FileBox URL: {url}")

    def extract(self) -> Generator[DownloadItem, None, None]:
        if self.content_type == "album":
            yield from self._extract_album()
        else:
            yield from self._extract_file()
```

### Implement extraction logic

```python
def _extract_album(self) -> Generator[DownloadItem, None, None]:
    response = self.session.get(
        f"{self.API_BASE}/albums/{self.content_id}",
        timeout=30
    )
    response.raise_for_status()

    data = response.json()
    album_name = data.get("name", self.content_id)

    for file_data in data.get("files", []):
        yield DownloadItem(
            download_url=file_data["download_url"],
            filename=file_data["filename"],
            collection_name=album_name,
            source_id=file_data["id"],
            size_bytes=file_data.get("size"),
        )

def _extract_file(self) -> Generator[DownloadItem, None, None]:
    response = self.session.get(
        f"{self.API_BASE}/files/{self.content_id}",
        timeout=30
    )
    response.raise_for_status()

    data = response.json()

    yield DownloadItem(
        download_url=data["download_url"],
        filename=data["filename"],
        source_id=data["id"],
        size_bytes=data.get("size"),
    )
```

### Add custom headers (optional)

If the platform requires specific headers:

```python
def _configure_session(self, session: requests.Session) -> None:
    session.headers.update({
        "Referer": "https://filebox.com/",
        "Origin": "https://filebox.com",
    })
```

### Add credential support (optional)

For platforms requiring authentication:

```python
import os

class FileBox(BasePlugin):
    def __init__(self, url: str, **options: Any) -> None:
        super().__init__(url, **options)

        # kwargs > env var
        self.api_key = self.options.get("api_key") or os.getenv("FILEBOX_API_KEY")
        self.content_type, self.content_id = self._parse_url(url)

    def _configure_session(self, session: requests.Session) -> None:
        session.headers["Referer"] = "https://filebox.com/"

        if self.api_key:
            session.headers["Authorization"] = f"Bearer {self.api_key}"
            logger.debug("Using FileBox API authentication")
```

### Register the plugin

Add your plugin to
[`packages/core/megaloader/plugins/__init__.py`](https://github.com/totallynotdavid/megaloader/blob/main/packages/core/megaloader/plugins/__init__.py):

```python
from megaloader.plugins.filebox import FileBox

PLUGIN_REGISTRY: dict[str, type[BasePlugin]] = {
    # ... existing plugins ...
    "filebox.com": FileBox,
}
```

## DownloadItem fields

When creating items:

**Required:**

- `download_url` (str) - Direct URL to download the file
- `filename` (str) - Original filename

**Optional:**

- `collection_name` (str | None) - Album/gallery/user grouping
- `source_id` (str | None) - Platform-specific identifier
- `headers` (dict[str, str]) - Additional HTTP headers needed for download
- `size_bytes` (int | None) - File size in bytes

**Example with all fields:**

```python
yield DownloadItem(
    download_url="https://cdn.filebox.com/files/abc123.jpg",
    filename="photo.jpg",
    collection_name="vacation_2024",
    source_id="abc123",
    headers={"Referer": "https://filebox.com/"},
    size_bytes=1024000,
)
```

## Session management

`BasePlugin` provides automatic session management:

**Lazy creation:** The session is created only when first accessed.

**Retry logic:** Sessions include automatic retries (3 attempts, exponential
backoff) for status codes 429, 500, 502, 503, 504.

**Default headers:** All sessions include a User-Agent header.

Add platform-specific headers in `_configure_session()`.

## Error handling

Let errors propagate naturally:

```python
def extract(self) -> Generator[DownloadItem, None, None]:
    # Good: Let errors propagate
    response = self.session.get(self.url, timeout=30)
    response.raise_for_status()

    data = response.json()

    for item in data["files"]:
        yield self._create_item(item)
```

The `extract()` function wraps plugin errors in `ExtractionError` automatically.

Validate input early and raise `ValueError` for invalid URLs:

```python
def __init__(self, url: str, **options: Any) -> None:
    super().__init__(url, **options)

    if not self._is_valid_url(url):
        raise ValueError(f"Invalid FileBox URL: {url}")
```

Use logging for debug information:

```python
import logging

logger = logging.getLogger(__name__)

def extract(self) -> Generator[DownloadItem, None, None]:
    logger.debug("Starting extraction for album: %s", self.content_id)
    response = self.session.get(url, timeout=30)
    logger.debug("Received %d files", len(response.json()["files"]))
```

## Common patterns

**Pagination:**

```python
def extract(self) -> Generator[DownloadItem, None, None]:
    page = 1

    while True:
        response = self.session.get(
            f"{self.API_BASE}/albums/{self.content_id}",
            params={"page": page},
            timeout=30
        )
        response.raise_for_status()

        files = response.json().get("files", [])
        if not files:
            break

        for file_data in files:
            yield self._create_item(file_data)

        page += 1
```

**Nested collections:**

```python
def extract(self) -> Generator[DownloadItem, None, None]:
    album_data = self._fetch_album(self.content_id)

    for gallery in album_data.get("galleries", []):
        for file_data in gallery["files"]:
            yield DownloadItem(
                download_url=file_data["url"],
                filename=file_data["name"],
                collection_name=f"{self.content_id}/{gallery['name']}",
            )
```

**Deduplication:**

```python
def extract(self) -> Generator[DownloadItem, None, None]:
    seen_urls: set[str] = set()

    for file_data in self._fetch_files():
        url = file_data["download_url"]

        if url in seen_urls:
            continue

        seen_urls.add(url)
        yield self._create_item(file_data)
```

**HTML parsing:**

```python
from bs4 import BeautifulSoup

def extract(self) -> Generator[DownloadItem, None, None]:
    response = self.session.get(self.url, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    for img in soup.select("div.gallery img"):
        if src := img.get("src"):
            yield DownloadItem(
                download_url=src,
                filename=src.split("/")[-1],
            )
```

## Testing

**Manual testing:**

```python
from megaloader.plugins.filebox import FileBox

plugin = FileBox("https://filebox.com/album/test123")
items = list(plugin.extract())

for item in items:
    print(f"{item.filename} - {item.download_url}")
```

**Integration testing:**

```python
import megaloader as mgl

for item in mgl.extract("https://filebox.com/album/test123"):
    print(item.filename)
```

**Unit tests** in `packages/core/tests/unit/`:

```python
import pytest
from megaloader.plugins.filebox import FileBox

def test_parse_album_url():
    plugin = FileBox("https://filebox.com/album/abc123")
    assert plugin.content_type == "album"
    assert plugin.content_id == "abc123"

def test_invalid_url():
    with pytest.raises(ValueError, match="Invalid FileBox URL"):
        FileBox("https://example.com/invalid")
```

**Live tests** in `packages/core/tests/live/`:

```python
import pytest
import megaloader as mgl

@pytest.mark.live
def test_filebox_extraction():
    items = list(mgl.extract("https://filebox.com/album/test123"))

    assert len(items) > 0
    assert all(item.download_url for item in items)
    assert all(item.filename for item in items)
```

## Best practices

Use type hints:

```python
from collections.abc import Generator
from typing import Any

def extract(self) -> Generator[DownloadItem, None, None]:
    ...
```

Add docstrings:

```python
def extract(self) -> Generator[DownloadItem, None, None]:
    """
    Extract files from FileBox albums and files.

    Yields:
        DownloadItem: Metadata for each file

    Raises:
        ValueError: Invalid URL format
        requests.HTTPError: Network request failed
    """
```

Use constants:

```python
class FileBox(BasePlugin):
    API_BASE = "https://api.filebox.com/v1"
    TIMEOUT = 30
```

Extract helper methods:

```python
def extract(self) -> Generator[DownloadItem, None, None]:
    data = self._fetch_album_data()

    for file_data in data["files"]:
        yield self._create_item(file_data)

def _fetch_album_data(self) -> dict[str, Any]:
    response = self.session.get(
        f"{self.API_BASE}/albums/{self.content_id}",
        timeout=self.TIMEOUT
    )
    response.raise_for_status()
    return response.json()
```

Handle missing data gracefully:

```python
yield DownloadItem(
    download_url=file_data["url"],
    filename=file_data.get("name", "unknown"),
    size_bytes=file_data.get("size"),  # None is fine
)
```

## Contributing

Once your plugin works:

1. Add tests (unit and live)
2. Update documentation (add platform to platforms.md)
3. Run linting (`ruff format` and `ruff check --fix`)
4. Run type checking (`mypy packages/core/megaloader`)
5. Submit a pull request

See the [Contributing Guide](/development/contributing) for details.
