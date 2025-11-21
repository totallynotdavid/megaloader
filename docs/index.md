# Megaloader Documentation

Welcome to the Megaloader documentation! This project will make you smile. 😊

Megaloader is a Python library for **extracting downloadable content metadata** from file hosting and media platforms. It discovers files and provides download URLs, filenames, and other metadata—**without performing the actual downloads**.

## What Megaloader Does

✅ **Extracts metadata** from 11+ file hosting platforms  
✅ **Discovers files** in albums, galleries, and collections  
✅ **Provides download URLs** with required headers and authentication  
✅ **Yields results lazily** using Python generators for memory efficiency  
✅ **Automatic plugin detection** based on URL domain

## What Megaloader Doesn't Do

❌ **Does not download files** - you implement downloads using the metadata  
❌ **Does not manage file storage** - you control where and how files are saved  
❌ **Does not handle rate limiting** - you implement retry logic as needed

This separation gives you full control over the download process, allowing you to implement custom logic for progress tracking, concurrent downloads, resume capabilities, and error handling.

## Quick Example

```python
import megaloader as mgl
import requests
from pathlib import Path

# Extract metadata from a URL
for item in mgl.extract("https://pixeldrain.com/l/abc123"):
    print(f"Found: {item.filename} ({item.size_bytes} bytes)")
    
    # You implement the download
    response = requests.get(item.download_url, headers=item.headers)
    response.raise_for_status()
    
    # Organize by collection if available
    output_dir = Path("downloads")
    if item.collection_name:
        output_dir = output_dir / item.collection_name
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save the file
    filepath = output_dir / item.filename
    filepath.write_bytes(response.content)
    print(f"Downloaded: {filepath}")
```

## Supported Platforms

| Platform    | Domain(s)                                    | Status      |
| ----------- | -------------------------------------------- | ----------- |
| Bunkr       | bunkr.si, bunkr.la, bunkr.is, bunkr.ru, bunkr.su | ✅ Core     |
| Cyberdrop   | cyberdrop.cr, cyberdrop.me, cyberdrop.to     | ✅ Core     |
| GoFile      | gofile.io                                    | ✅ Core     |
| PixelDrain  | pixeldrain.com                               | ✅ Core     |
| Fanbox      | fanbox.cc (with subdomains)                  | ⚠️ Extended |
| Fapello     | fapello.com                                  | ⚠️ Extended |
| Pixiv       | pixiv.net                                    | ⚠️ Extended |
| Rule34      | rule34.xxx                                   | ⚠️ Extended |
| Thotslife   | thotslife.com                                | ⚠️ Extended |
| Thothub.to  | thothub.to, thothub.ch                       | ⚠️ Extended |
| Thothub.vip | thothub.vip                                  | ⚠️ Extended |

**Core platforms** receive active development and testing. **Extended platforms** are maintained on a best-effort basis.

## Try It Out

Test the package by downloading a file (max 4mb):

<script setup>
import DemoComponent from './Demo.vue'
</script>

<DemoComponent />

## Getting Started

Check out the [Installation Guide](getting-started/installation.md) to get
started, or jump straight to the [Quick Start](getting-started/quickstart.md)
for examples.

## Components

This monorepo contains:

- **Core Library** (`megaloader`): Python library for metadata extraction - [PyPI](https://pypi.org/project/megaloader/)
- **CLI Tool** (`megaloader-cli`): Command-line interface with built-in download functionality
- **API** (`megaloader-api`): FastAPI demo server for documentation examples

## Links

- [GitHub Repository](https://github.com/totallynotdavid/megaloader)
- [Issue Tracker](https://github.com/totallynotdavid/megaloader/issues)
- [PyPI Package](https://pypi.org/project/megaloader/)
