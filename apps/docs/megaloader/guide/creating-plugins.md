# Creating plugins

This guide walks through creating a plugin for a new platform.

## Plugin architecture

Megaloader uses a registry pattern to map domains to plugin classes. To add
support for a new platform, you create a class that inherits from `BasePlugin`
and implements the extraction logic.

A plugin performs no network I/O of its own. The engine resolves the URL to a
plugin, builds a `Fetcher`, and passes it to `extract()`. The plugin describes
each request as a `Request` and reads back a `Response`, so parsing and
traversal stay testable offline.

In other words, every plugin:

1. Inherits from `BasePlugin`
2. Implements `extract(fetch)` to yield `DownloadItem` objects
3. Optionally overrides `session_config()` to declare site headers and auth
   cookies
4. Gets registered in `PLUGIN_REGISTRY` (in `registry.py`) to map domains to the
   plugin

## Minimal example

Your plugin must implement the `extract` method and yield `DownloadItem`
objects. Route every network call through the `fetch` argument.

```python
from collections.abc import Generator

from megaloader.fetcher import Fetcher, Request
from megaloader.item import DownloadItem
from megaloader.plugin import BasePlugin

class SimpleHost(BasePlugin):
    def extract(self, fetch: Fetcher) -> Generator[DownloadItem, None, None]:
        data = fetch(Request(self.url)).json()

        for file_data in data["files"]:
            yield DownloadItem(
                download_url=file_data["url"],
                filename=file_data["name"],
                size_bytes=file_data.get("size"),
            )
```

That's it. The `Fetcher` handles session creation, retries, default headers, and
mapping request failures to `ExtractionError`. Your plugin just describes
requests and yields `DownloadItem` objects.

What the engine provides:

- `self.url`: the URL passed to the plugin
- `self.options`: dictionary of keyword arguments
- `fetch`: a `Fetcher` that resolves a `Request` to a `Response`, with retries
  and error handling built in. Always route network calls through it. Don't
  reimplement retry logic.

What you implement:

- `extract(fetch)`: must yield `DownloadItem` objects
- `session_config()`: optional, declares site headers and auth cookies

A `Request` carries `url`, `method` (default `"GET"`), `params`, `json`,
`headers`, and `allow_redirects`. A `Response` exposes `url`, `status_code`,
`text`, `content`, and `json()`.

## Building a plugin

Let's build a plugin for a fictional platform called "FileBox" that has album
URLs like `https://filebox.com/album/abc123` and file URLs like
`https://filebox.com/file/xyz789`.

Start by creating the plugin class and parsing the URL:

```python{14}
import logging
import re
from collections.abc import Generator
from typing import Any

from megaloader.fetcher import Fetcher, Request
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

    def extract(self, fetch: Fetcher) -> Generator[DownloadItem, None, None]:
        if self.content_type == "album":
            yield from self._extract_album(fetch)
        else:
            yield from self._extract_file(fetch)
```

Implement album extraction:

```python
def _extract_album(self, fetch: Fetcher) -> Generator[DownloadItem, None, None]:
    data = fetch(Request(f"{self.API_BASE}/albums/{self.content_id}")).json()
    album_name = data.get("name", self.content_id)

    for file_data in data.get("files", []):
        yield DownloadItem(
            download_url=file_data["download_url"],
            filename=file_data["filename"],
            collection_name=album_name,
            source_id=file_data["id"],
            size_bytes=file_data.get("size"),
        )
```

For single files:

```python
def _extract_file(self, fetch: Fetcher) -> Generator[DownloadItem, None, None]:
    data = fetch(Request(f"{self.API_BASE}/files/{self.content_id}")).json()

    yield DownloadItem(
        download_url=data["download_url"],
        filename=data["filename"],
        source_id=data["id"],
        size_bytes=data.get("size"),
    )
```

If the platform requires specific headers, override `session_config()`:

```python
from megaloader.fetcher import SessionConfig

def session_config(self) -> SessionConfig:
    return SessionConfig(headers={
        "Referer": "https://filebox.com/",
        "Origin": "https://filebox.com",
    })
```

Finally, register your plugin in
`packages/core/megaloader/plugins/registry.py`. Add the import, then map the
domains in `PLUGIN_REGISTRY` and the plugin name in `PLUGIN_NAME_REGISTRY`:

```python
from megaloader.plugins.filebox import FileBox

PLUGIN_REGISTRY: dict[str, type[BasePlugin]] = {
    # ... existing plugins ...
    "filebox.com": FileBox,
    "filebox.cc": FileBox,  # other domains with the same structure
}

PLUGIN_NAME_REGISTRY: dict[str, type[BasePlugin]] = {
    # ... existing plugins ...
    "filebox": FileBox,
}
```

Now you can use it:

```python
import megaloader as mgl

for item in mgl.extract("https://filebox.com/album/test123"):
    print(item.filename)
```

## Adding authentication

For platforms requiring authentication, accept credentials through options or
environment variables, then apply them in `session_config()`:

```python{12}
import os

from megaloader.fetcher import SessionConfig

class FileBox(BasePlugin):
    def __init__(self, url: str, **options: Any) -> None:
        super().__init__(url, **options)

        # Prefer explicit option, fall back to environment variable
        self.api_key = self.options.get("api_key") or os.getenv("FILEBOX_API_KEY")
        self.content_type, self.content_id = self._parse_url(url)

    def session_config(self) -> SessionConfig:
        headers = {"Referer": "https://filebox.com/"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return SessionConfig(headers=headers)
```

When the credential is a cookie rather than a header (as with Pixiv), declare it
with `Cookie` instead:

```python
from megaloader.fetcher import Cookie, SessionConfig

def session_config(self) -> SessionConfig:
    cookies = ()
    if self.api_key:
        cookies = (Cookie("session", self.api_key, ".filebox.com"),)
    return SessionConfig(cookies=cookies)
```

Users can then pass credentials:

```python
mgl.extract("https://filebox.com/album/test", api_key="your-key")
```

Or set the environment variable:

```bash
export FILEBOX_API_KEY="your-key"
```

## DownloadItem fields

When creating items, you must provide:

- `download_url` (str): direct download URL
- `filename` (str): original leaf filename, no path separators

Optional fields:

- `collection_name` (str | None): album/gallery/user grouping
- `source_id` (str | None): platform-specific identifier
- `headers` (dict[str, str]): additional HTTP headers needed for download
- `size_bytes` (int | None): file size in bytes

Example with all fields:

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

## Common patterns

Handle pagination within `extract` so the consumer sees a single continuous
stream of items. This is useful when an API returns results in multiple pages,
as is the case with the Rule34 plugin.

```python
def extract(self, fetch: Fetcher) -> Generator[DownloadItem, None, None]:
    page = 1

    while True:
        request = Request(
            f"{self.API_BASE}/albums/{self.content_id}",
            params={"page": page},
        )
        files = fetch(request).json().get("files", [])
        if not files:
            break

        for file_data in files:
            yield self._create_item(file_data)

        page += 1
```

Nested collections (when albums contain sub-galleries):

```python
def extract(self, fetch: Fetcher) -> Generator[DownloadItem, None, None]:
    album_data = self._fetch_album(fetch, self.content_id)

    for gallery in album_data.get("galleries", []):
        for file_data in gallery["files"]:
            yield DownloadItem(
                download_url=file_data["url"],
                filename=file_data["name"],
                collection_name=f"{self.content_id}/{gallery['name']}",
            )
```

Deduplication (when a host supports uploading files with the same name):

```python
def extract(self, fetch: Fetcher) -> Generator[DownloadItem, None, None]:
    seen_urls: set[str] = set()

    for file_data in self._fetch_files(fetch):
        url = file_data["download_url"]

        if url in seen_urls:
            continue

        seen_urls.add(url)
        yield self._create_item(file_data)
```

HTML parsing (when there's no API):

```python
from bs4 import BeautifulSoup

def extract(self, fetch: Fetcher) -> Generator[DownloadItem, None, None]:
    soup = BeautifulSoup(fetch(Request(self.url)).text, "html.parser")

    for img in soup.select("div.gallery img"):
        if src := img.get("src"):
            yield DownloadItem(
                download_url=str(src),
                filename=str(src).split("/")[-1],
            )
```

## Error handling

Let errors propagate naturally. `RequestsFetcher` raises `ExtractionError` on
HTTP and network failures, and the top-level `extract()` wraps any other
unexpected error in `ExtractionError` too.

```python
def extract(self, fetch: Fetcher) -> Generator[DownloadItem, None, None]:
    data = fetch(Request(self.url)).json()

    for item in data["files"]:
        yield self._create_item(item)
```

When the response parses but its shape is wrong, raise with context using
`raise_extraction_error` so the failure carries a source and URL:

```python
from megaloader.error_policy import raise_extraction_error

def extract(self, fetch: Fetcher) -> Generator[DownloadItem, None, None]:
    data = fetch(Request(self.url)).json()

    if "files" not in data:
        raise_extraction_error(
            "Unexpected API response: missing 'files'",
            source=self.source,
            url=self.url,
            category="protocol",
        )

    for item in data["files"]:
        yield self._create_item(item)
```

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

def extract(self, fetch: Fetcher) -> Generator[DownloadItem, None, None]:
    logger.debug("Starting extraction for album: %s", self.content_id)
    data = fetch(Request(f"{self.API_BASE}/albums/{self.content_id}")).json()
    logger.debug("Received %d files", len(data["files"]))
```

## Testing your plugin

See [Testing plugins](testing-plugins) for manual testing, writing unit tests,
and recording cassettes.

## Best practices

Use type hints for better IDE support and type checking:

```python
from collections.abc import Generator
from typing import Any

def extract(self, fetch: Fetcher) -> Generator[DownloadItem, None, None]:
    ...
```

Add docstrings to document behaviour:

```python
def extract(self, fetch: Fetcher) -> Generator[DownloadItem, None, None]:
    """
    Extract files from FileBox albums and files.

    Yields:
        DownloadItem: Metadata for each file

    Raises:
        ValueError: Invalid URL format
        ExtractionError: Network request or parsing failed
    """
```

Use constants for magic values:

```python
class FileBox(BasePlugin):
    API_BASE = "https://api.filebox.com/v1"
```

Extract helper methods to keep code readable:

```python
def extract(self, fetch: Fetcher) -> Generator[DownloadItem, None, None]:
    data = self._fetch_album_data(fetch)

    for file_data in data["files"]:
        yield self._create_item(file_data)
```

Handle missing data:

```python
yield DownloadItem(
    download_url=file_data["url"],
    filename=file_data.get("name", "unknown"),
    size_bytes=file_data.get("size"),  # None is fine
)
```

## Contributing

Once your plugin works:

1. Add tests ([see Testing plugins](testing-plugins))
2. Update documentation (add to platforms.md)
3. Run linting: `ruff format` and `ruff check --fix`
4. Run type checking: `mypy packages/core/megaloader`
5. Submit a pull request

See the [Contributing Guide](../development/contributing.md) for details.
