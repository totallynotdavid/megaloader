# [pkg]: megaloader (core)

[![PyPI version](https://badge.fury.io/py/megaloader.svg)](https://badge.fury.io/py/megaloader)
[![CodeQL](https://github.com/totallynotdavid/megaloader/actions/workflows/codeql.yml/badge.svg)](https://github.com/totallynotdavid/megaloader/actions/workflows/codeql.yml)
[![lint and format check](https://github.com/totallynotdavid/megaloader/actions/workflows/checks.yml/badge.svg)](https://github.com/totallynotdavid/megaloader/actions/workflows/checks.yml)
[![codecov](https://codecov.io/gh/totallynotdavid/megaloader/graph/badge.svg?token=SBHAGJJB8L)](https://codecov.io/gh/totallynotdavid/megaloader)

Library for extracting downloadable content metadata from file hosting
platforms. Provides automatic URL detection and a plugin architecture for
multi-platform support.

## Installation

```bash
pip install megaloader
```

The library has minimal dependencies: `requests` for HTTP, `beautifulsoup4` and
`lxml` for HTML parsing.

## Basic usage

Call `extract()` with any supported URL. The function detects the platform
automatically and returns a generator of file metadata:

```python
from megaloader import extract

for item in extract("https://pixeldrain.com/l/abc123"):
    print(f"{item.filename} - {item.download_url}")
```

Each item contains the download URL, filename, and optional metadata like
collection name and file size. Network requests happen lazily during iteration.

## Downloading files

The library extracts metadata only. Use `requests` or similar to download:

```python
import requests
from pathlib import Path
from megaloader import extract

def download_file(item, output_dir):
    dest = Path(output_dir) / item.filename
    response = requests.get(item.download_url, headers=item.headers, stream=True)
    response.raise_for_status()

    with open(dest, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

for item in extract("https://pixeldrain.com/l/abc123"):
    download_file(item, "./downloads")
```

The `headers` attribute contains any required HTTP headers for the download
request.

## Supported platforms

Four core platforms receive active development. Seven extended platforms are
maintained best-effort and may break without immediate fixes.

**Core platforms**:

Bunkr (bunkr.si, bunkr.la, bunkr.is, bunkr.ru, bunkr.su), PixelDrain
(pixeldrain.com), Cyberdrop (cyberdrop.cr, cyberdrop.me, cyberdrop.to), GoFile
(gofile.io).

**Extended platforms**:

Fanbox ({creator}.fanbox.cc), Pixiv (pixiv.net), Rule34 (rule34.xxx), ThotsLife
(thotslife.com), ThotHub.VIP (thothub.vip), ThotHub.TO (thothub.to), Fapello
(fapello.com).

All platforms support albums, galleries, or lists. Single-file URLs work where
applicable.

Extended platforms marked as working as of November 2025.

## Platform-specific features

GoFile supports password-protected folders through the password parameter:

```python
items = extract("https://gofile.io/d/folder", password="secret123")
```

Fanbox and Pixiv require session cookies for full results. Without
authentication, only limited data is returned:

```python
items = extract("https://creator.fanbox.cc", session_id="your_session_cookie")
items = extract("https://pixiv.net/artworks/12345", session_id="your_session_cookie")
```

Rule34 accepts optional API credentials for higher rate limits:

```python
items = extract(
    "https://rule34.xxx/index.php?page=post&s=list&tags=example",
    api_key="your_api_key",
    user_id="your_user_id"
)
```

Authentication improves results but is not required.

<!-- prettier-ignore -->
> [!WARNING]  
> Free-tier accounts on Pixiv and Fanbox may still return incomplete file sets.

## Working with items

The `DownloadItem` dataclass contains file metadata:

```python
for item in extract(url):
    item.download_url     # Direct download URL (required)
    item.filename         # Original filename (required)
    item.collection_name  # Album/gallery name (optional)
    item.source_id        # Platform-specific ID (optional)
    item.size_bytes       # File size in bytes (optional)
    item.headers          # Required HTTP headers (optional)
```

Required fields are always populated. Optional fields may be `None` depending on
platform and content type.

## Direct plugin usage

Import plugin classes directly when you need fine-grained control or want to
force a specific plugin:

```python
from megaloader.plugins import Cyberdrop

plugin = Cyberdrop("https://cyberdrop.me/a/album_id")
items = list(plugin.extract())
print(f"Found {len(items)} files")
```

This bypasses automatic detection. Useful when a platform introduces new domains
before the package updates.

## Error handling

Handle extraction failures as needed:

```python
from megaloader import extract, ExtractionError, UnsupportedDomainError

try:
    items = list(extract(url))
except UnsupportedDomainError:
    print("Platform not supported")
except ExtractionError as e:
    print(f"Extraction failed: {e}")
except ValueError:
    print("Invalid URL format")
```

Network failures raise `ExtractionError`. Unsupported URLs raise
`UnsupportedDomainError`. Malformed URLs raise `ValueError`.

## API reference

The `extract()` function takes a URL and platform-specific options. Returns a
generator of `DownloadItem` objects. Raises `ValueError` for invalid URLs,
`UnsupportedDomainError` when no plugin exists, `ExtractionError` on network or
parsing failures.

The `DownloadItem` dataclass has required fields `download_url` and `filename`.
Optional fields are `collection_name`, `source_id`, `size_bytes`, and `headers`.

The `BasePlugin` abstract class defines the plugin interface. Override
`extract()` to yield items. Override `_configure_session()` to add custom
headers or authentication. The `session` property provides a configured requests
session. The `url` and `options` properties contain constructor arguments.

Exception hierarchy: `ExtractionError` for network and parsing failures,
`UnsupportedDomainError` for unknown domains, both inherit from `Exception`.

## Contributing

The project welcomes contributions. Install dependencies with `uv sync` from the
repository root. Run `uv run ruff format .` and `uv run mypy packages/core`
before committing. See the repository contributing guide for plugin development
details.

Report bugs and request features through GitHub Discussions. Include Python
version, error messages, and problematic URLs.
