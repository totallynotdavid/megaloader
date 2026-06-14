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

You can also force a plugin explicitly:

```python
for item in extract("https://example.invalid/path", plugin="gofile"):
    print(item.filename)
```

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

## API options

`extract()` accepts optional transport and plugin controls:

```python
import requests
from megaloader import extract
from megaloader.plugins.gofile import Gofile

session = requests.Session()

# Force plugin by name
items = extract("https://example.invalid/path", plugin="gofile")

# Force plugin by class
items = extract("https://example.invalid/path", plugin=Gofile)

# Inject your own session and timeout
items = extract("https://gofile.io/d/fhGIJu", session=session, timeout=20)
```

This keeps extraction in core while letting downstream apps decide transport
policy.

## Supported platforms

Four core platforms receive active development. Seven extended platforms are
maintained best-effort and may break without immediate fixes.

**Core platforms**:

Bunkr (bunkr.si, bunkr.la, bunkr.is, bunkr.ru, bunkr.su), PixelDrain
(pixeldrain.com), Cyberdrop (cyberdrop.cr, cyberdrop.me, cyberdrop.to), GoFile
(gofile.io).

**Extended platforms**:

Pixiv (pixiv.net), Rule34 (rule34.xxx), ThotsLife (thotslife.com), ThotHub.VIP
(thothub.vip), ThotHub.TO (thothub.to), Fapello (fapello.com).

All platforms support albums, galleries, or lists. Single-file URLs work where
applicable.

## Platform-specific features

GoFile supports password-protected folders:

```python
items = extract("https://gofile.io/d/folder", password="secret123")
```

Pixiv requires a session cookie for full results. Without authentication, only
public content is returned (which is very limited):

```python
items = extract("https://pixiv.net/artworks/12345", session_id="your_session_cookie")
```

Rule34 accepts optional API credentials for higher rate limits and faster
extraction. Without them, scraping is used as a fallback:

```python
items = extract(
    "https://rule34.xxx/index.php?page=post&s=list&tags=example",
    api_key="your_api_key",
    user_id="your_user_id"
)
```

<!-- prettier-ignore -->
> [!WARNING]  
> Free-tier accounts on Pixiv may still return incomplete file sets.

## Working with items

The `DownloadItem` dataclass contains file metadata:

```python
for item in extract(url):
    item.download_url     # Direct download URL (required)
    item.filename         # Leaf filename only (required, no path separators)
    item.collection_name  # Album/gallery name (optional)
    item.source_id        # Platform-specific ID (optional)
    item.size_bytes       # File size in bytes (optional)
    item.headers          # Required HTTP headers (optional)
```

Required fields are always populated. Optional fields may be `None` depending on
platform and content type.

## Direct plugin usage

Import plugin classes directly when you need plugin-specific control:

```python
from megaloader.plugins.cyberdrop import Cyberdrop

plugin = Cyberdrop("https://cyberdrop.me/a/album_id")
items = list(plugin.extract())
print(f"Found {len(items)} files")
```

This bypasses automatic detection and gives direct access to plugin internals.

## Error handling

Then use commas and make the sentence structurally explicit instead of
interruptive.

Best version without em dashes:

All extraction failures surface as typed exceptions. Malformed URLs raise
`ValueError`. Unknown hosts raise `UnsupportedDomainError`. All other failures,
including HTTP errors, network failures, and unexpected API responses, raise
`ExtractionError` with structured metadata:

```python
from megaloader import (
    ExtractionError,
    UnsupportedDomainError,
    extract,
)

try:
    items = list(extract(url))
except UnsupportedDomainError:
    print("Platform not supported")
except ExtractionError as e:
    print(f"Extraction failed: {e.detail}")
    print(f"source={e.source} category={e.category} http={e.http_status}")
except ValueError:
    print("Invalid URL format")
```

`ExtractionError.category` is one of `"rate_limit"`, `"auth"`, `"access"`,
`"network"`, `"timeout"`, `"protocol"`, or `"unknown"`. HTTP status codes are
classified automatically: a 429 always surfaces as `"rate_limit"`, a 401 as
`"auth"`, and so on, regardless of which plugin handled the request.

## Writing a plugin

Subclass `BasePlugin` and implement `extract()`:

```python
from collections.abc import Generator
from megaloader.plugin import BasePlugin
from megaloader.item import DownloadItem

class MyPlugin(BasePlugin):
    def _configure_session(self, session):
        session.headers["Referer"] = "https://example.com/"

    def extract(self) -> Generator[DownloadItem, None, None]:
        response = self._get(self.url)  # raises ExtractionError on failure
        data = response.json()
        for file in data["files"]:
            yield DownloadItem(
                download_url=file["url"],
                filename=file["name"],
            )
```

Use `self._get(url)` and `self._post(url, ...)` instead of the session directly.
Both methods map HTTP and network failures to `ExtractionError` automatically,
so `extract()` only needs to handle business logic. Override
`_configure_session()` to add authentication headers or cookies.

## Contributing

Install dependencies with `uv sync` from the repository root. Run
`mise run check` before committing; it covers formatting, type checking, and
unit tests. See the repository contributing guide for plugin development
details.

Report bugs and request features through GitHub Discussions. Include Python
version, error messages, and problematic URLs.
