---
title: Basic usage
description: Learn the fundamentals of using megaloader to extract file metadata, access item fields, and handle plugin-specific options.
outline: [2, 3]
prev:
  text: 'User guide overview'
  link: '/guide/'
next:
  text: 'Download implementation'
  link: '/guide/download-implementation'
---

# Basic usage

This guide covers the fundamentals of using Megaloader to extract file metadata from supported platforms.

[[toc]]

## Simple extraction

The most basic usage is calling `extract()` with a URL:

```python
import megaloader as mgl

for item in mgl.extract("https://pixeldrain.com/l/abc123"):
    print(item.filename)
```

This returns a generator that yields `DownloadItem` objects as they're discovered.

## Accessing item metadata

Each `DownloadItem` contains metadata about a downloadable file:

```python
import megaloader as mgl

for item in mgl.extract("https://pixeldrain.com/l/abc123"):
    # Essential fields
    print(f"URL: {item.download_url}")
    print(f"Filename: {item.filename}")
    
    # Optional fields (may be None)
    print(f"Size: {item.size_bytes} bytes")
    print(f"Collection: {item.collection_name}")
    print(f"Source ID: {item.source_id}")
    
    # HTTP headers needed for download
    print(f"Headers: {item.headers}")
```

### DownloadItem fields

| Field | Type | Description |
|-------|------|-------------|
| `download_url` | `str` | Direct URL to download the file |
| `filename` | `str` | Original filename from the platform |
| `collection_name` | `str \| None` | Album, gallery, or user name for grouping |
| `source_id` | `str \| None` | Platform-specific unique identifier |
| `headers` | `dict[str, str]` | HTTP headers required for download (e.g., Referer) |
| `size_bytes` | `int \| None` | File size in bytes (if available) |

## Collecting all items

Since `extract()` returns a generator, you can collect all items into a list:

```python
import megaloader as mgl

# Collect all items at once
items = list(mgl.extract("https://pixeldrain.com/l/abc123"))

print(f"Found {len(items)} files")

# Now you can iterate multiple times
for item in items:
    print(item.filename)
```

::: warning Memory usage
Collecting all items into a list loads all metadata into memory. For large galleries with thousands of files, consider processing items one at a time instead.
:::

## Plugin-specific options

Some platforms require additional parameters like passwords or authentication tokens.

### Password-protected content

GoFile supports password-protected folders:

```python
import megaloader as mgl

# Pass password as a keyword argument
for item in mgl.extract(
    "https://gofile.io/d/abc123",
    password="secret123"
):
    print(item.filename)
```

### Session authentication

Platforms like Fanbox and Pixiv require session cookies for authentication:

```python
import megaloader as mgl

# Fanbox requires session_id cookie
for item in mgl.extract(
    "https://creator.fanbox.cc/posts/123456",
    session_id="your_session_cookie_value"
):
    print(item.filename)

# Pixiv also uses session_id
for item in mgl.extract(
    "https://pixiv.net/artworks/123456",
    session_id="your_pixiv_session"
):
    print(item.filename)
```

### API authentication

Rule34 supports optional API authentication for higher rate limits:

```python
import megaloader as mgl

# Optional API key and user ID
for item in mgl.extract(
    "https://rule34.xxx/index.php?page=post&s=list&tags=example",
    api_key="your_api_key",
    user_id="your_user_id"
):
    print(item.filename)
```

::: tip Environment variables
Most plugins also support environment variables as fallback credentials. See [plugin options](/plugins/plugin-options) for details.
:::

## Error handling

Handle common errors gracefully:

```python
import megaloader as mgl

try:
    for item in mgl.extract(url):
        print(item.filename)
        
except mgl.UnsupportedDomainError as e:
    print(f"Platform not supported: {e.domain}")
    print("See supported platforms: https://totallynotdavid.megaloader.com/plugins/supported-platforms")
    
except mgl.ExtractionError as e:
    print(f"Failed to extract: {e}")
    print("This could be due to:")
    print("  - Network connectivity issues")
    print("  - Invalid or expired URL")
    print("  - Missing authentication credentials")
    print("  - Platform changes breaking the plugin")
    
except ValueError as e:
    print(f"Invalid input: {e}")
```

### Exception types

| Exception | When it's raised |
|-----------|------------------|
| `UnsupportedDomainError` | URL domain has no plugin available |
| `ExtractionError` | Network failure or parsing error during extraction |
| `ValueError` | Invalid URL format or empty URL |

## Checking URLs before extraction

Validate URLs before attempting extraction:

```python
import megaloader as mgl
from urllib.parse import urlparse

def is_supported(url: str) -> bool:
    """Check if URL domain is supported."""
    try:
        domain = urlparse(url).netloc
        # Try to get plugin class
        from megaloader.plugins import get_plugin_class
        return get_plugin_class(domain) is not None
    except Exception:
        return False

# Check before extracting
url = "https://example.com/file"
if is_supported(url):
    items = list(mgl.extract(url))
else:
    print("URL not supported")
```

## Filtering during extraction

Process items selectively during iteration:

```python
import megaloader as mgl

# Only process image files
for item in mgl.extract(url):
    if item.filename.lower().endswith(('.jpg', '.png', '.gif')):
        print(f"Image: {item.filename}")

# Only process files larger than 1MB
for item in mgl.extract(url):
    if item.size_bytes and item.size_bytes > 1_000_000:
        print(f"Large file: {item.filename} ({item.size_bytes} bytes)")

# Stop after finding 10 items
count = 0
for item in mgl.extract(url):
    print(item.filename)
    count += 1
    if count >= 10:
        break
```

## Working with collections

Many platforms organize files into collections (albums, galleries, user pages):

```python
import megaloader as mgl
from collections import defaultdict

# Group items by collection
collections = defaultdict(list)

for item in mgl.extract(url):
    collection = item.collection_name or "uncategorized"
    collections[collection].append(item)

# Print summary
for collection_name, items in collections.items():
    print(f"{collection_name}: {len(items)} files")
```

## Simple download example

Combine extraction with basic downloading:

```python
import megaloader as mgl
import requests
from pathlib import Path

def download_all(url: str, output_dir: str = "./downloads"):
    """Extract and download all files from URL."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    for item in mgl.extract(url):
        # Download file
        response = requests.get(item.download_url, headers=item.headers)
        response.raise_for_status()
        
        # Save to disk
        filepath = output_path / item.filename
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        print(f"Downloaded: {filepath}")

# Usage
download_all("https://pixeldrain.com/l/abc123")
```

::: tip Advanced downloads
For production use, see [download implementation](/core/download-implementation) for examples with progress bars, retry logic, and concurrent downloads.
:::
