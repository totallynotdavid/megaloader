---
title: API reference
description: Complete API reference for megaloader including extract(), DownloadItem, BasePlugin, exceptions, and plugin registry.
outline: [2, 4]
prev:
  text: 'Advanced usage'
  link: '/guide/advanced-usage'
---

# API reference

Complete reference documentation for the Megaloader core library API.

[[toc]]

## Functions

### extract()

Extract downloadable items from a URL.

```python
def extract(url: str, **options: Any) -> Generator[DownloadItem, None, None]: ...
```

Returns a generator that yields items lazily as they're discovered. Network requests happen during iteration, not at call time.

**Parameters:**

- `url` (str): The source URL to extract from
- `**options` (Any): Plugin-specific options (see below)

**Returns:**

- `Generator[DownloadItem, None, None]`: Generator yielding DownloadItem objects

**Raises:**

- `ValueError`: Invalid URL format or empty URL
- `UnsupportedDomainError`: No plugin available for the URL's domain
- `ExtractionError`: Network or parsing failure during extraction

**Plugin-specific options:**

| Option | Type | Plugins | Description |
|--------|------|---------|-------------|
| `password` | str | Gofile | Password for protected content |
| `session_id` | str | Fanbox, Pixiv | Session cookie for authentication |
| `api_key` | str | Rule34 | API key for authenticated requests |
| `user_id` | str | Rule34 | User ID for authenticated requests |

**Example:**

```python
import megaloader as mgl

# Basic usage
for item in mgl.extract("https://pixeldrain.com/l/abc123"):
    print(item.filename)

# With password
for item in mgl.extract("https://gofile.io/d/xyz789", password="secret"):
    print(item.filename)

# With session authentication
for item in mgl.extract(
    "https://creator.fanbox.cc/posts/123456",
    session_id="your_session_cookie"
):
    print(item.filename)
```

## Classes

### DownloadItem

Dataclass representing metadata for a single downloadable file.

```python
@dataclass
class DownloadItem:
    download_url: str
    filename: str
    collection_name: str | None = None
    source_id: str | None = None
    headers: dict[str, str] = field(default_factory=dict)
    size_bytes: int | None = None
```

**Attributes:**

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| `download_url` | str | Yes | Direct URL to download the file |
| `filename` | str | Yes | Original filename (may need sanitization) |
| `collection_name` | str \| None | No | Optional grouping (album/gallery/user) |
| `source_id` | str \| None | No | Optional unique identifier from source platform |
| `headers` | dict[str, str] | No | HTTP headers required for download (e.g., Referer) |
| `size_bytes` | int \| None | No | File size in bytes (if available) |

**Validation:**

The `__post_init__` method validates that `download_url` and `filename` are not empty. Raises `ValueError` if validation fails.

**Example:**

```python
import megaloader as mgl

for item in mgl.extract("https://pixeldrain.com/l/abc123"):
    # Access all fields
    print(f"URL: {item.download_url}")
    print(f"Filename: {item.filename}")
    print(f"Size: {item.size_bytes} bytes")
    print(f"Collection: {item.collection_name}")
    print(f"Source ID: {item.source_id}")
    print(f"Headers: {item.headers}")
```

### BasePlugin

Abstract base class for platform-specific extractors.

```python
class BasePlugin(ABC):
    DEFAULT_HEADERS: ClassVar[dict[str, str]]
    
    def __init__(self, url: str, **options: Any) -> None: ...
    
    @property
    def session(self) -> requests.Session: ...
    
    def _configure_session(self, session: requests.Session) -> None: ...
    
    @abstractmethod
    def extract(self) -> Generator[DownloadItem, None, None]: ...
```

**Class attributes:**

- `DEFAULT_HEADERS`: Default User-Agent header for HTTP requests

**Instance attributes:**

- `url` (str): The URL being extracted from
- `options` (dict): Plugin-specific options passed to constructor

**Methods:**

#### `__init__(url, **options)`

Initialize plugin with URL and options.

**Parameters:**
- `url` (str): Source URL to extract from
- `**options` (Any): Plugin-specific options

**Raises:**
- `ValueError`: If URL is empty

#### `session` (property)

Lazily-created requests session with retry logic and default headers.

**Returns:**
- `requests.Session`: Configured session object

The session includes:
- Default User-Agent header
- Retry strategy for transient failures (3 retries with exponential backoff)
- Automatic retry on status codes: 429, 500, 502, 503, 504

#### `_configure_session(session)`

Override to add plugin-specific headers or authentication.

**Parameters:**
- `session` (requests.Session): Session to configure

**Example:**
```python
def _configure_session(self, session: requests.Session) -> None:
    session.headers["Referer"] = f"https://{self.domain}/"
    if api_key := os.getenv("PLUGIN_API_KEY"):
        session.headers["Authorization"] = f"Bearer {api_key}"
```

#### `extract()` (abstract)

Extract downloadable items from the URL. Must be implemented by subclasses.

**Returns:**
- `Generator[DownloadItem, None, None]`: Generator yielding items

**Raises:**
- `ExtractionError`: On network or parsing failures

**Example implementation:**
```python
def extract(self) -> Generator[DownloadItem, None, None]:
    response = self.session.get(self.url)
    response.raise_for_status()
    
    # Parse response and yield items
    for file_data in parse_response(response.text):
        yield DownloadItem(
            download_url=file_data["url"],
            filename=file_data["name"],
            size_bytes=file_data.get("size"),
        )
```

## Exceptions

### MegaloaderError

Base exception for all Megaloader errors.

```python
class MegaloaderError(Exception):
    """Base exception for all megaloader errors."""
```

All Megaloader-specific exceptions inherit from this class.

### ExtractionError

Failed to extract items due to network or parsing error.

```python
class ExtractionError(MegaloaderError):
    """Failed to extract items from URL due to network or parsing error."""
```

**Common causes:**
- Network connectivity issues
- Invalid or expired URLs
- Missing authentication credentials
- Platform changes breaking the plugin
- Rate limiting or blocking

**Example:**
```python
import megaloader as mgl

try:
    items = list(mgl.extract(url))
except mgl.ExtractionError as e:
    print(f"Extraction failed: {e}")
```

### UnsupportedDomainError

No plugin available for the URL's domain.

```python
class UnsupportedDomainError(MegaloaderError):
    def __init__(self, domain: str) -> None:
        super().__init__(f"No plugin found for domain: {domain}")
        self.domain = domain
```

**Attributes:**
- `domain` (str): The unsupported domain

**Example:**
```python
import megaloader as mgl

try:
    items = list(mgl.extract("https://unsupported-site.com/file"))
except mgl.UnsupportedDomainError as e:
    print(f"Domain not supported: {e.domain}")
    print("See supported platforms at: https://docs.megaloader.com/plugins/supported-platforms")
```

## Plugin registry

### get_plugin_class()

Resolve domain to plugin class.

```python
def get_plugin_class(domain: str) -> type[BasePlugin] | None: ...
```

**Parameters:**
- `domain` (str): Normalized domain from URL (e.g., "pixiv.net")

**Returns:**
- `type[BasePlugin] | None`: Plugin class or None if unsupported

**Resolution order:**
1. Exact match in PLUGIN_REGISTRY
2. Subdomain match for supported domains (e.g., creator.fanbox.cc → fanbox.cc)
3. Partial match fallback (e.g., www.pixiv.net → pixiv.net)

**Example:**
```python
from megaloader.plugins import get_plugin_class

# Check if domain is supported
plugin_class = get_plugin_class("pixeldrain.com")
if plugin_class:
    print(f"Supported: {plugin_class.__name__}")
else:
    print("Not supported")
```

### PLUGIN_REGISTRY

Dictionary mapping domains to plugin classes.

```python
PLUGIN_REGISTRY: dict[str, type[BasePlugin]]
```

**Example:**
```python
from megaloader.plugins import PLUGIN_REGISTRY

# List all supported domains
for domain in sorted(PLUGIN_REGISTRY.keys()):
    print(domain)
```

## Type hints

Megaloader uses type hints throughout the codebase. Import types for type checking:

```python
from megaloader import DownloadItem, ExtractionError, UnsupportedDomainError
from megaloader.plugin import BasePlugin
from collections.abc import Generator
from typing import Any

def process_items(url: str) -> list[DownloadItem]:
    """Extract and return all items."""
    return list(extract(url))

def custom_extractor(url: str, **options: Any) -> Generator[DownloadItem, None, None]:
    """Custom extraction wrapper."""
    try:
        yield from extract(url, **options)
    except ExtractionError:
        # Handle error
        pass
```

## Version information

Get the current library version:

```python
import megaloader

print(megaloader.__version__)  # e.g., "0.2.0"
```

## Module exports

The top-level `megaloader` module exports:

```python
__all__ = [
    "DownloadItem",
    "ExtractionError", 
    "UnsupportedDomainError",
    "extract"
]
```

**Recommended import style:**

```python
# Import as namespace (recommended)
import megaloader as mgl

items = list(mgl.extract(url))

# Import specific items
from megaloader import extract, DownloadItem

for item in extract(url):
    print(item.filename)

# Import exceptions
from megaloader import ExtractionError, UnsupportedDomainError

try:
    items = list(extract(url))
except UnsupportedDomainError:
    print("Domain not supported")
except ExtractionError:
    print("Extraction failed")
```

## Environment variables

Some plugins support environment variables as fallback credentials:

| Variable | Plugin | Description |
|----------|--------|-------------|
| `GOFILE_PASSWORD` | Gofile | Default password for protected content |
| `FANBOX_SESSION_ID` | Fanbox | Session cookie for authentication |
| `PIXIV_SESSION_ID` | Pixiv | Session cookie for authentication |
| `RULE34_API_KEY` | Rule34 | API key for authenticated requests |
| `RULE34_USER_ID` | Rule34 | User ID for authenticated requests |

**Precedence:** Explicit kwargs passed to `extract()` take precedence over environment variables.

**Example:**

```bash
# Set environment variable
export GOFILE_PASSWORD="secret123"
```

```python
import megaloader as mgl

# Uses environment variable
items = list(mgl.extract("https://gofile.io/d/abc123"))

# Explicit password overrides environment variable
items = list(mgl.extract("https://gofile.io/d/abc123", password="different"))
```

## Logging

Megaloader uses Python's standard logging module. Enable debug logging to see detailed extraction information:

```python
import logging
import megaloader as mgl

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Now extraction will log detailed information
for item in mgl.extract("https://pixeldrain.com/l/abc123"):
    print(item.filename)
```

**Log Levels:**
- `DEBUG`: Detailed extraction information, HTTP requests
- `INFO`: General information about extraction progress
- `WARNING`: Recoverable issues
- `ERROR`: Extraction failures
