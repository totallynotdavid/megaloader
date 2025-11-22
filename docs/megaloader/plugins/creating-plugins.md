---
title: Creating custom plugins
description: Step-by-step guide to building custom Megaloader plugins for new platforms with examples and best practices.
outline: [2, 4]
prev:
  text: 'Plugin options'
  link: '/plugins/plugin-options'
next:
  text: 'Contributing'
  link: '/development/contributing'
---

# Creating Custom plugins

This guide walks you through creating a custom plugin for a new platform. By the end, you'll understand the plugin architecture and be able to add support for any file hosting platform.

[[toc]]

## Plugin architecture overview

Every plugin in Megaloader:

1. **Inherits from `BasePlugin`** - provides session management and retry logic
2. **Implements `extract()`** - yields `DownloadItem` objects as files are discovered
3. **Optionally overrides `_configure_session()`** - adds platform-specific headers/auth
4. **Gets registered in `PLUGIN_REGISTRY`** - maps domains to the plugin class

## Minimal plugin example

Here's the simplest possible plugin:

```python
from collections.abc import Generator
from megaloader.item import DownloadItem
from megaloader.plugin import BasePlugin


class SimpleHost(BasePlugin):
    """Extract files from SimpleHost."""

    def extract(self) -> Generator[DownloadItem, None, None]:
        """Extract downloadable items from the URL."""
        # Make HTTP request
        response = self.session.get(self.url, timeout=30)
        response.raise_for_status()
        
        # Parse response (example: JSON API)
        data = response.json()
        
        # Yield items
        for file_data in data["files"]:
            yield DownloadItem(
                download_url=file_data["url"],
                filename=file_data["name"],
                size_bytes=file_data.get("size"),
            )
```

That's it! The `BasePlugin` class handles session creation, retry logic, and default headers automatically.

## BasePlugin class reference

### Provided attributes

- **`self.url`** - The URL passed to `extract()`
- **`self.options`** - Dictionary of keyword arguments (e.g., `password`, `session_id`)
- **`self.session`** - Lazy-loaded `requests.Session` with retry logic

### Provided methods

- **`_create_session()`** - Creates session with retry strategy (don't override)
- **`_configure_session(session)`** - Override to add custom headers/cookies

### Required implementation

- **`extract()`** - Must yield `DownloadItem` objects

## Building a real plugin

Let's build a plugin for a fictional platform called "FileBox" that has:
- Album URLs: `https://filebox.com/album/abc123`
- File URLs: `https://filebox.com/file/xyz789`
- JSON API at `https://api.filebox.com/v1/`

### Step 1: Create the plugin class

```python
import logging
import re
from collections.abc import Generator
from typing import Any

from megaloader.item import DownloadItem
from megaloader.plugin import BasePlugin

logger = logging.getLogger(__name__)


class FileBox(BasePlugin):
    """Extract files from FileBox albums and individual files."""

    API_BASE = "https://api.filebox.com/v1"

    def __init__(self, url: str, **options: Any) -> None:
        super().__init__(url, **options)
        
        # Parse URL to determine content type and ID
        self.content_type, self.content_id = self._parse_url(url)

    def _parse_url(self, url: str) -> tuple[str, str]:
        """Extract content type and ID from URL."""
        if match := re.search(r"filebox\.com/(album|file)/([\w-]+)", url):
            return match.group(1), match.group(2)
        
        msg = f"Invalid FileBox URL: {url}"
        raise ValueError(msg)

    def extract(self) -> Generator[DownloadItem, None, None]:
        """Extract downloadable items from the URL."""
        if self.content_type == "album":
            yield from self._extract_album()
        else:
            yield from self._extract_file()
```

### Step 2: Implement extraction logic

```python
def _extract_album(self) -> Generator[DownloadItem, None, None]:
    """Extract all files from an album."""
    # Fetch album metadata
    response = self.session.get(
        f"{self.API_BASE}/albums/{self.content_id}",
        timeout=30
    )
    response.raise_for_status()
    
    data = response.json()
    album_name = data.get("name", self.content_id)
    
    # Yield each file
    for file_data in data.get("files", []):
        yield DownloadItem(
            download_url=file_data["download_url"],
            filename=file_data["filename"],
            collection_name=album_name,
            source_id=file_data["id"],
            size_bytes=file_data.get("size"),
        )

def _extract_file(self) -> Generator[DownloadItem, None, None]:
    """Extract a single file."""
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

### Step 3: Add custom headers (optional)

If the platform requires specific headers:

```python
def _configure_session(self, session: requests.Session) -> None:
    """Add FileBox-specific headers."""
    session.headers.update({
        "Referer": "https://filebox.com/",
        "Origin": "https://filebox.com",
    })
```

### Step 4: Add credential support (optional)

If the platform requires authentication:

```python
import os

class FileBox(BasePlugin):
    def __init__(self, url: str, **options: Any) -> None:
        super().__init__(url, **options)
        
        # Credentials: kwargs > env var
        self.api_key = self.options.get("api_key") or os.getenv("FILEBOX_API_KEY")
        
        self.content_type, self.content_id = self._parse_url(url)

    def _configure_session(self, session: requests.Session) -> None:
        """Add authentication if available."""
        session.headers["Referer"] = "https://filebox.com/"
        
        if self.api_key:
            session.headers["Authorization"] = f"Bearer {self.api_key}"
            logger.debug("Using FileBox API authentication")
```

### Step 5: Register the plugin

Add your plugin to the registry in `packages/core/megaloader/plugins/__init__.py`:

```python
from megaloader.plugins.filebox import FileBox

PLUGIN_REGISTRY: dict[str, type[BasePlugin]] = {
    # ... existing plugins ...
    "filebox.com": FileBox,
}
```

## DownloadItem fields

When creating `DownloadItem` objects, you can provide:

### Required fields

- **`download_url`** (str) - Direct URL to download the file
- **`filename`** (str) - Original filename

### Optional fields

- **`collection_name`** (str | None) - Album/gallery/user grouping for organization
- **`source_id`** (str | None) - Platform-specific unique identifier
- **`headers`** (dict[str, str]) - Additional HTTP headers needed for download
- **`size_bytes`** (int | None) - File size in bytes

### Example with all fields

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

The `BasePlugin` class provides automatic session management:

### Lazy session creation

The session is created only when first accessed:

```python
# Session doesn't exist yet
plugin = FileBox(url)

# Session is created on first use
response = plugin.session.get(url)  # Creates session here
```

### Automatic retry logic

Sessions include retry logic for transient failures:

- **Retries**: 3 attempts with exponential backoff
- **Status codes**: 429, 500, 502, 503, 504
- **Methods**: GET and POST

You don't need to implement retry logic yourself—it's handled automatically.

### Default headers

All sessions include:

```python
{
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}
```

Add platform-specific headers in `_configure_session()`.

## Error handling

### Let errors propagate

Don't catch exceptions in `extract()`—let them propagate naturally:

```python
def extract(self) -> Generator[DownloadItem, None, None]:
    # ✅ Good: Let errors propagate
    response = self.session.get(self.url, timeout=30)
    response.raise_for_status()  # Raises on HTTP errors
    
    data = response.json()  # Raises on invalid JSON
    
    for item in data["files"]:
        yield self._create_item(item)
```

The `extract()` function in `megaloader/__init__.py` wraps plugin errors in `ExtractionError` automatically.

### Validate input early

Raise `ValueError` for invalid URLs or missing parameters:

```python
def __init__(self, url: str, **options: Any) -> None:
    super().__init__(url, **options)
    
    if not self._is_valid_url(url):
        msg = f"Invalid FileBox URL: {url}"
        raise ValueError(msg)
```

### Log debug information

Use logging for debugging without cluttering output:

```python
import logging

logger = logging.getLogger(__name__)

def extract(self) -> Generator[DownloadItem, None, None]:
    logger.debug("Starting extraction for album: %s", self.content_id)
    
    response = self.session.get(url, timeout=30)
    logger.debug("Received %d files", len(response.json()["files"]))
    
    # ... yield items
```

## Testing your plugin

### Manual testing

Test your plugin directly:

```python
from megaloader.plugins.filebox import FileBox

plugin = FileBox("https://filebox.com/album/test123")
items = list(plugin.extract())

for item in items:
    print(f"{item.filename} - {item.download_url}")
```

### Integration testing

Test through the main `extract()` function:

```python
import megaloader as mgl

for item in mgl.extract("https://filebox.com/album/test123"):
    print(item.filename)
```

### Unit tests

Create tests in `packages/core/tests/unit/`:

```python
import pytest
from megaloader.plugins.filebox import FileBox


def test_parse_album_url():
    plugin = FileBox("https://filebox.com/album/abc123")
    assert plugin.content_type == "album"
    assert plugin.content_id == "abc123"


def test_parse_file_url():
    plugin = FileBox("https://filebox.com/file/xyz789")
    assert plugin.content_type == "file"
    assert plugin.content_id == "xyz789"


def test_invalid_url():
    with pytest.raises(ValueError, match="Invalid FileBox URL"):
        FileBox("https://example.com/invalid")
```

### Live tests

Create live tests in `packages/core/tests/live/` (marked with `@pytest.mark.live`):

```python
import pytest
import megaloader as mgl


@pytest.mark.live
def test_filebox_album_extraction():
    """Test extraction from a real FileBox album."""
    items = list(mgl.extract("https://filebox.com/album/test123"))
    
    assert len(items) > 0
    assert all(item.download_url for item in items)
    assert all(item.filename for item in items)
```

Run live tests with:

```bash
pytest packages/core/tests --run-live
```

## Common patterns

### Pagination

Handle paginated APIs:

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
        
        data = response.json()
        files = data.get("files", [])
        
        if not files:
            break  # No more pages
        
        for file_data in files:
            yield self._create_item(file_data)
        
        page += 1
```

### Nested collections

Handle galleries within albums:

```python
def extract(self) -> Generator[DownloadItem, None, None]:
    # Get album metadata
    album_data = self._fetch_album(self.content_id)
    
    # Extract galleries
    for gallery in album_data.get("galleries", []):
        gallery_name = gallery["name"]
        
        # Extract files from each gallery
        for file_data in gallery["files"]:
            yield DownloadItem(
                download_url=file_data["url"],
                filename=file_data["name"],
                collection_name=f"{self.content_id}/{gallery_name}",
            )
```

### Deduplication

Avoid yielding duplicate files:

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

### HTML parsing

Use BeautifulSoup for HTML scraping:

```python
from bs4 import BeautifulSoup

def extract(self) -> Generator[DownloadItem, None, None]:
    response = self.session.get(self.url, timeout=30)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, "html.parser")
    
    # Find all image links
    for img in soup.select("div.gallery img"):
        if src := img.get("src"):
            filename = src.split("/")[-1]
            yield DownloadItem(
                download_url=src,
                filename=filename,
            )
```

## Best practices

### Use type hints

```python
from collections.abc import Generator
from typing import Any

def extract(self) -> Generator[DownloadItem, None, None]:
    ...

def _parse_url(self, url: str) -> tuple[str, str]:
    ...
```

### Add docstrings

```python
def extract(self) -> Generator[DownloadItem, None, None]:
    """
    Extract files from FileBox albums and individual files.
    
    Yields:
        DownloadItem: Metadata for each file found
        
    Raises:
        ValueError: Invalid URL format
        requests.HTTPError: Network request failed
    """
```

### Use constants

```python
class FileBox(BasePlugin):
    API_BASE = "https://api.filebox.com/v1"
    MAX_RETRIES = 3
    TIMEOUT = 30
```

### Extract helper methods

```python
def extract(self) -> Generator[DownloadItem, None, None]:
    data = self._fetch_album_data()
    
    for file_data in data["files"]:
        yield self._create_item(file_data)

def _fetch_album_data(self) -> dict[str, Any]:
    """Fetch album metadata from API."""
    response = self.session.get(
        f"{self.API_BASE}/albums/{self.content_id}",
        timeout=self.TIMEOUT
    )
    response.raise_for_status()
    return response.json()

def _create_item(self, file_data: dict[str, Any]) -> DownloadItem:
    """Create DownloadItem from API response."""
    return DownloadItem(
        download_url=file_data["url"],
        filename=file_data["name"],
        size_bytes=file_data.get("size"),
    )
```

### Handle missing data gracefully

```python
yield DownloadItem(
    download_url=file_data["url"],  # Required
    filename=file_data.get("name", "unknown"),  # Fallback
    size_bytes=file_data.get("size"),  # Optional (None is fine)
)
```

## Contributing your plugin

Once your plugin is working:

1. **Add tests** - Both unit and live tests
2. **Update documentation** - Add platform to supported-platforms.md
3. **Run linting** - `ruff format` and `ruff check --fix`
4. **Run type checking** - `mypy packages/core/megaloader`
5. **Submit a pull request** - Include example URLs and test results

See [Contributing Guide](../development/contributing.md) for detailed instructions.
