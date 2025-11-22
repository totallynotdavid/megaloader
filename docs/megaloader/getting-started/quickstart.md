---
title: Quick start
description: Get started with megaloader in 5 minutes. Learn to extract metadata and download files from file hosting platforms.
outline: [2, 3]
prev:
  text: 'Installation'
  link: '/getting-started/installation'
next:
  text: 'User guide'
  link: '/guide/'
---

# Quick start

Get started with Megaloader in 5 minutes!

## What is megaloader?

Megaloader extracts downloadable file metadata from file hosting platforms. It **does not download files**, instead, it gives you the URLs, filenames, and other metadata so you can implement downloads however you want.

## Basic extraction

The simplest way to use Megaloader is with the `extract()` function:

```python
import megaloader as mgl

# Extract metadata from a URL
for item in mgl.extract("https://pixeldrain.com/l/abc123"):
    print(f"File: {item.filename}")
    print(f"URL: {item.download_url}")
    print(f"Size: {item.size_bytes} bytes")
    print()
```

The `extract()` function returns a generator that yields `DownloadItem` objects containing metadata for each file.

## Accessing DownloadItem fields

Each `DownloadItem` has the following fields:

```python
for item in mgl.extract("https://cyberdrop.me/a/example"):
    # Required fields
    print(item.download_url)    # Direct download URL
    print(item.filename)         # Original filename
    
    # Optional fields
    print(item.collection_name)  # Album/gallery name (if applicable)
    print(item.source_id)        # Platform-specific ID (if available)
    print(item.headers)          # Required HTTP headers (dict)
    print(item.size_bytes)       # File size in bytes (if available)
```

## Simple Download implementation

To actually download files, use the metadata from `DownloadItem`:

```python
import megaloader as mgl
import requests
from pathlib import Path

# Extract and download
for item in mgl.extract("https://pixeldrain.com/u/example"):
    # Download the file
    response = requests.get(item.download_url, headers=item.headers)
    
    # Save to disk
    filepath = Path("./downloads") / item.filename
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_bytes(response.content)
    
    print(f"Downloaded: {item.filename}")
```

## Using the CLI

If you installed the CLI package, you can use Megaloader from the terminal:

### Extract metadata (dry run)

See what would be downloaded without actually downloading:

```bash
megaloader extract "https://pixeldrain.com/l/abc123"
```

Output in JSON format:

```bash
megaloader extract "https://pixeldrain.com/l/abc123" --json
```

### Download files

Download all files to a directory:

```bash
megaloader download "https://pixeldrain.com/l/abc123" ./downloads
```

By default, files are organized into subfolders by collection. Use `--flat` to disable this:

```bash
megaloader download "https://pixeldrain.com/l/abc123" ./downloads --flat
```

### List supported platforms

```bash
megaloader plugins
```

## Plugin-specific options

Some platforms require additional options like passwords or authentication:

::: code-group

```python [GoFile with Password]
import megaloader as mgl

# Gofile with password
for item in mgl.extract("https://gofile.io/d/abc123", password="secret"):
    print(item.filename)
```

```python [Pixiv with Session]
import megaloader as mgl

# Pixiv with session cookie
for item in mgl.extract("https://pixiv.net/user/123", session_id="your_cookie"):
    print(item.filename)
```

```bash [CLI with Password]
megaloader download "https://gofile.io/d/abc123" ./downloads --password secret
```

:::

## Error handling

Handle common errors gracefully:

```python
import megaloader as mgl

try:
    items = list(mgl.extract("https://example.com/file"))
except mgl.UnsupportedDomainError as e:
    print(f"Domain not supported: {e.domain}")
except mgl.ExtractionError as e:
    print(f"Extraction failed: {e}")
except ValueError as e:
    print(f"Invalid URL: {e}")
```

::: tip Error Handling
Always wrap extraction in try-except blocks to handle network failures and unsupported domains gracefully.
:::

## Complete example

Here's a complete example with error handling and progress tracking:

```python
import megaloader as mgl
import requests
from pathlib import Path

def download_from_url(url: str, output_dir: str = "./downloads") -> None:
    """Extract and download all files from a URL."""
    try:
        # Extract metadata
        items = list(mgl.extract(url))
        print(f"Found {len(items)} files")
        
        # Download each file
        for i, item in enumerate(items, 1):
            print(f"[{i}/{len(items)}] Downloading {item.filename}...")
            
            # Determine output path
            if item.collection_name:
                output_path = Path(output_dir) / item.collection_name
            else:
                output_path = Path(output_dir)
            
            output_path.mkdir(parents=True, exist_ok=True)
            filepath = output_path / item.filename
            
            # Download file
            response = requests.get(item.download_url, headers=item.headers)
            response.raise_for_status()
            filepath.write_bytes(response.content)
            
            print(f"  ✓ Saved to {filepath}")
            
    except mgl.UnsupportedDomainError as e:
        print(f"Error: Domain '{e.domain}' is not supported")
    except mgl.ExtractionError as e:
        print(f"Error: Failed to extract metadata - {e}")
    except Exception as e:
        print(f"Error: {e}")

# Use it
download_from_url("https://pixeldrain.com/l/abc123")
```
