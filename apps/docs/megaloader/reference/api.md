# API reference

Complete reference for the Megaloader core library.

## Functions

### extract()

Extract downloadable items from a URL. Primary entry point. Dispatches the URL
to the appropriate plugin.

```python
def extract(url: str, **options: Any) -> Generator[DownloadItem, None, None]
```

Returns a generator that yields items lazily as they're discovered. Network
requests happen during iteration.

**Parameters:**

- `url` (str) - Source URL to extract from
- `**options` (Any) - Plugin-specific options

**Returns:** Generator yielding `DownloadItem` objects

**Raises:**

- `ValueError` - Invalid or empty URL
- `UnsupportedDomainError` - No plugin available for the domain
- `ExtractionError` - Network or parsing failure

**Example:**

```python
import megaloader as mgl

# Basic usage
for item in mgl.extract("https://pixeldrain.com/l/abc123"):
    print(item.filename)

# With password
for item in mgl.extract("https://gofile.io/d/xyz789", password="secret"):
    print(item.filename)
```

::: details Output

```
sample-image-01.jpg
sample-image-02.jpg
sample-image-03.jpg
sample-image-04.jpg
sample-image-05.jpg
sample-image-06.jpg
```

:::

## Classes

### DownloadItem

Dataclass representing file metadata for a downloadable file.

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

**Fields:**

| Field             | Type           | Required | Description                        |
| ----------------- | -------------- | -------- | ---------------------------------- |
| `download_url`    | str            | Yes      | Direct download URL                |
| `filename`        | str            | Yes      | Original filename                  |
| `collection_name` | str \| None    | No       | Album/gallery/user grouping        |
| `source_id`       | str \| None    | No       | Platform-specific identifier       |
| `headers`         | dict[str, str] | No       | Required HTTP headers for download |
| `size_bytes`      | int \| None    | No       | File size in bytes                 |

The `__post_init__` method validates that `download_url` and `filename` are not
empty.

**Example:**

```python
for item in mgl.extract(url):
    print(f"URL: {item.download_url}")
    print(f"Name: {item.filename}")
    print(f"Size: {item.size_bytes}")
    print(f"Collection: {item.collection_name}")
    print(f"Headers: {item.headers}")
```

::: details Output

```
URL: https://pixeldrain.com/api/file/WnQte6cf
Name: sample-image-01.jpg
Size: 207558
Collection: None
Headers: {}
```

:::

### BasePlugin

Abstract base class for platform extractors. A plugin performs no network I/O of
its own. It describes each request as a `Request` and reads back a `Response`
through an injected `Fetcher`, so parsing and traversal stay testable offline.

```python
class BasePlugin(ABC):
    def __init__(self, url: str, **options: Any) -> None

    @property
    def source(self) -> str

    def session_config(self) -> SessionConfig

    @abstractmethod
    def extract(self, fetch: Fetcher) -> Generator[DownloadItem, None, None]
```

**Attributes:**

- `url` (str): URL being extracted from
- `options` (dict): plugin-specific options

#### source (property)

Lowercase plugin name used to tag extraction errors.

**Returns:** `str`

#### session_config()

Override to declare site headers and auth cookies the fetcher should apply.
Default returns an empty `SessionConfig`.

**Returns:** `SessionConfig`

**Example:**

```python
def session_config(self) -> SessionConfig:
    cookies = ()
    if api_key := os.getenv("PLUGIN_API_KEY"):
        cookies = (Cookie("token", api_key, ".example.com"),)
    return SessionConfig(headers={"Referer": "https://example.com/"}, cookies=cookies)
```

#### extract(fetch) (abstract)

Yield downloadable items, fetching pages lazily through `fetch`. Must be
implemented by subclasses.

**Parameters:** `fetch` (Fetcher): resolves a `Request` to a `Response`

**Returns:** Generator yielding `DownloadItem` objects

**Raises:** `ExtractionError` on network or parsing failures

### Fetcher

The single seam that performs network I/O. Production code uses
`RequestsFetcher`; tests pass a function that returns canned `Response` objects
to exercise a plugin's full traversal offline.

```python
class Fetcher(Protocol):
    def __call__(self, request: Request) -> Response: ...
```

`RequestsFetcher` wraps a `requests.Session` and owns the default User-Agent,
retries (2 attempts, exponential backoff on 429, 500, 502, 503, 504), and the
mapping from request failures to `ExtractionError` tagged with the plugin name.

## Exceptions

### MegaloaderError

Base exception for all Megaloader errors.

```python
class MegaloaderError(Exception):
    pass
```

All library exceptions inherit from this.

### ExtractionError

Failed to extract items due to network or parsing error.

```python
class ExtractionError(MegaloaderError):
    pass
```

**Common causes:** Network issues, invalid URLs, missing authentication,
platform changes breaking the plugin, rate limiting.

**Example:**

```python
try:
    items = list(mgl.extract(url))
except mgl.ExtractionError as e:
    print(f"Extraction failed: {e}")
```

### UnsupportedDomainError

No plugin available for the domain.

```python
class UnsupportedDomainError(MegaloaderError):
    def __init__(self, domain: str) -> None:
        super().__init__(f"No plugin found for domain: {domain}")
        self.domain = domain
```

**Attributes:** `domain` (str) - The unsupported domain

**Example:**

```python
try:
    items = list(mgl.extract("https://unsupported-site.com/file"))
except mgl.UnsupportedDomainError as e:
    print(f"Domain not supported: {e.domain}")
```

## Plugin registry

### get_plugin_for_domain()

Resolve domain to plugin class.

```python
def get_plugin_for_domain(domain: str) -> type[BasePlugin] | None
```

**Parameters:** `domain` (str) - Normalized domain

**Returns:** Plugin class or None

**Resolution order:** Exact match, then subdomain match.

**Example:**

```python
from megaloader.plugins import get_plugin_for_domain

plugin_class = get_plugin_for_domain("pixeldrain.com")
if plugin_class:
    print(f"Supported: {plugin_class.__name__}")
```

::: details Output

```
Supported: PixelDrain
```

:::

### PLUGIN_REGISTRY

Dictionary mapping domains to plugin classes.

```python
PLUGIN_REGISTRY: dict[str, type[BasePlugin]]
```

**Example:**

```python
from megaloader.plugins import PLUGIN_REGISTRY

for domain in sorted(PLUGIN_REGISTRY.keys()):
    print(domain)
```

## Module exports

```python
__all__ = [
    "DownloadItem",
    "ExtractionError",
    "UnsupportedDomainError",
    "extract"
]
```

**Recommended import:**

```python
import megaloader as mgl

items = list(mgl.extract(url))
```

## Environment variables

| Variable          | Plugin | Description    |
| ----------------- | ------ | -------------- |
| `GOFILE_TOKEN`    | Gofile | Account token  |
| `PIXIV_PHPSESSID` | Pixiv  | Session cookie |
| `RULE34_API_KEY`  | Rule34 | API key        |
| `RULE34_USER_ID`  | Rule34 | User ID        |

Explicit kwargs take precedence.

## Logging

Enable debug logging:

```python
import logging

logging.basicConfig(level=logging.DEBUG)
```

**Levels:** DEBUG (detailed extraction), INFO (progress), WARNING (recoverable
issues), ERROR (failures).

## Version

```python
import megaloader

print(megaloader.__version__)
```
