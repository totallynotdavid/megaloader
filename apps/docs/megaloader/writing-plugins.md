# Writing plugins

A plugin teaches Megaloader one platform. It subclasses `BasePlugin`, turns a
URL into requests, and yields `DownloadItem` objects.

A plugin does no network I/O of its own. `extract()` builds a `Fetcher` and
passes it to the plugin's `extract(fetch)` method. The plugin describes each
request as a `Request` and reads the `Response` that comes back. The fetcher
owns the session, the retries, the default headers, and the mapping of failed
requests to `ExtractionError`. That seam is what lets [tests](testing-plugins)
run a plugin with canned responses.

| Name            | Fields                                                                     |
| --------------- | -------------------------------------------------------------------------- |
| `Request`       | `url`, `method="GET"`, `params`, `json`, `headers`, `allow_redirects=True` |
| `Response`      | `url`, `status_code`, `text`, `content`, and `json()`                      |
| `SessionConfig` | `headers`, and `cookies` as a tuple of `Cookie(name, value, domain)`       |

`Response.json()` raises an `ExtractionError` with category `protocol` when the
body is not JSON.

A plugin has these members:

| Member                     | Role                                                                        |
| -------------------------- | --------------------------------------------------------------------------- |
| `__init__(url, **options)` | Optional. Validate the URL and read options. Call `super().__init__` first. |
| `self.url`, `self.options` | The stripped URL, and the keyword options passed to `extract()`.            |
| `self.source`              | The lowercase class name. It tags errors.                                   |
| `session_config()`         | Optional. Returns the headers and cookies the platform needs.               |
| `extract(fetch)`           | Required. Yields `DownloadItem` objects.                                    |

## Example

This plugin reads a fictional platform, FileBox, with album URLs such as
`https://filebox.com/album/abc123` and file URLs such as
`https://filebox.com/file/xyz789`. It lives in
`packages/core/megaloader/plugins/filebox.py`:

```python
import logging
import re

from collections.abc import Generator
from typing import Any

from megaloader.error_policy import raise_extraction_error
from megaloader.fetcher import Fetcher, Request, SessionConfig
from megaloader.item import DownloadItem
from megaloader.plugin import BasePlugin


logger = logging.getLogger(__name__)


class FileBox(BasePlugin):
    """Extract files from FileBox albums and single files."""

    API_BASE = "https://api.filebox.com/v1"

    def __init__(self, url: str, **options: Any) -> None:
        super().__init__(url, **options)
        match = re.search(r"filebox\.com/(album|file)/([\w-]+)", self.url)
        if not match:
            msg = f"Unrecognized FileBox URL, expected /album/ or /file/: {self.url}"
            raise ValueError(msg)
        self.kind, self.content_id = match.groups()

    def session_config(self) -> SessionConfig:
        return SessionConfig(headers={"Referer": "https://filebox.com/"})

    def extract(self, fetch: Fetcher) -> Generator[DownloadItem, None, None]:
        if self.kind == "file":
            data = fetch(Request(f"{self.API_BASE}/files/{self.content_id}")).json()
            yield self._item(data, collection_name=None)
            return

        data = fetch(Request(f"{self.API_BASE}/albums/{self.content_id}")).json()
        if "files" not in data:
            raise_extraction_error(
                "Unexpected API response: missing 'files'",
                source=self.source,
                url=self.url,
                category="protocol",
            )

        name = data.get("name", self.content_id)
        logger.debug("Album %s has %d files", self.content_id, len(data["files"]))
        for file_data in data["files"]:
            yield self._item(file_data, collection_name=name)

    def _item(self, data: dict[str, Any], collection_name: str | None) -> DownloadItem:
        return DownloadItem(
            download_url=data["download_url"],
            filename=data["filename"],
            collection_name=collection_name,
            source_id=data.get("id"),
            size_bytes=data.get("size"),
        )
```

Pass the class to `extract()` to try it without registering it:

```python
import megaloader as mgl

for item in mgl.extract("https://filebox.com/album/abc123", plugin=FileBox):
    print(item.filename)
```

## Errors

- Raise `ValueError` for a URL the plugin cannot read. Do it in `__init__` or at
  the top of `extract()`.
- Let `ExtractionError` from the fetcher propagate.
- When a response arrives but has the wrong shape, call
  `raise_extraction_error(detail, source=..., url=..., category="protocol")`
  from `megaloader.error_policy`. It builds an `ExtractionError` with the
  category set. See [Errors](errors) for the categories.
- To stop on an expected failure, catch `ExtractionError` and inspect
  `http_status`. `thothub_to.py` ends model pagination on a `404` this way.

`extract()` wraps any other exception a plugin raises, except `ValueError`, in
an `ExtractionError` with category `unknown`.

## Authentication

Read credentials from `self.options`, fall back to an environment variable, and
apply them in `session_config()`. A cookie takes a `Cookie`:

```python
import os

from megaloader.fetcher import Cookie, SessionConfig


def session_config(self) -> SessionConfig:
    api_key = self.options.get("api_key") or os.getenv("FILEBOX_API_KEY")
    cookies = (Cookie("session", api_key, ".filebox.com"),) if api_key else ()
    return SessionConfig(
        headers={"Referer": "https://filebox.com/"}, cookies=cookies
    )
```

A caller passes the option as `mgl.extract(url, api_key="...")`.

## Pagination and traversal

Fetch further pages inside `extract()` so the caller sees one stream of items.
Because `extract()` is a generator, stop fetching when the caller stops
iterating:

```python
page = 1
while True:
    request = Request(f"{self.API_BASE}/albums/{self.content_id}", params={"page": page})
    files = fetch(request).json().get("files", [])
    if not files:
        break
    for file_data in files:
        yield self._item(file_data, collection_name=None)
    page += 1
```

When a platform has no API, parse HTML with
`BeautifulSoup(response.text, "html.parser")`. Deduplicate with a `seen` set
when pages overlap.

## DownloadItem

`download_url` and `filename` are required. `filename` is a leaf name: it cannot
contain `/`, `\`, or `..`.
`megaloader.filenames.filename_from_url(url, fallback)` derives one from a URL
path. Set `headers` when the download itself needs a `Referer` or other header,
as Bunkr does. `collection_name`, `source_id`, and `size_bytes` are optional.
Other fields are described in [Library](library).

## Register the plugin

Register the class in `packages/core/megaloader/plugins/registry.py`: import it,
add every domain to `PLUGIN_REGISTRY`, and its name to `PLUGIN_NAME_REGISTRY`.

```python
from megaloader.plugins.filebox import FileBox

PLUGIN_REGISTRY = {
    "filebox.com": FileBox,
}

PLUGIN_NAME_REGISTRY = {
    "filebox": FileBox,
}
```

A platform whose subdomains all belong to the plugin, as with Pixiv, also goes
in `SUBDOMAIN_SUPPORTED`.

Then add the platform to [Platforms](platforms) and
[Plugin options](plugin-options), add tests
([Testing plugins](testing-plugins)), and follow the
[contributing guide](https://github.com/totallynotdavid/megaloader/blob/main/.github/CONTRIBUTING.md).
