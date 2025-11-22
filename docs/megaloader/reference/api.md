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

### BasePlugin

Abstract base class for platform extractors.

```python
class BasePlugin(ABC):
    DEFAULT_HEADERS: ClassVar[dict[str, str]]

    def __init__(self, url: str, **options: Any) -> None

    @property
    def session(self) -> requests.Session

    def _configure_session(self, session: requests.Session) -> None

    @abstractmethod
    def extract(self) -> Generator[DownloadItem, None, None]
```

**Attributes:**

- `DEFAULT_HEADERS` - Default User-Agent header
- `url` (str) - URL being extracted from
- `options` (dict) - Plugin-specific options

#### session (property)

Lazily-created requests session with retry logic.

**Returns:** `requests.Session`

Includes default User-Agent, retry strategy (3 retries, exponential backoff),
and automatic retry on 429, 500, 502, 503, 504.

#### \_configure_session(session)

Override to add platform-specific headers or authentication.

**Parameters:** `session` (requests.Session)

**Example:**

```python
def _configure_session(self, session: requests.Session) -> None:
    session.headers["Referer"] = f"https://{self.domain}/"
    if api_key := os.getenv("PLUGIN_API_KEY"):
        session.headers["Authorization"] = f"Bearer {api_key}"
```

#### extract() (abstract)

Extract downloadable items from URL. Must be implemented by subclasses.

**Returns:** Generator yielding `DownloadItem` objects

**Raises:** `ExtractionError` on network or parsing failures

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

### get_plugin_class()

Resolve domain to plugin class.

```python
def get_plugin_class(domain: str) -> type[BasePlugin] | None
```

**Parameters:** `domain` (str) - Normalized domain

**Returns:** Plugin class or None

**Resolution order:** Exact match, subdomain match, partial match fallback.

**Example:**

```python
from megaloader.plugins import get_plugin_class

plugin_class = get_plugin_class("pixeldrain.com")
if plugin_class:
    print(f"Supported: {plugin_class.__name__}")
```

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

| Variable            | Plugin | Description      |
| ------------------- | ------ | ---------------- |
| `GOFILE_PASSWORD`   | Gofile | Default password |
| `FANBOX_SESSION_ID` | Fanbox | Session cookie   |
| `PIXIV_SESSION_ID`  | Pixiv  | Session cookie   |
| `RULE34_API_KEY`    | Rule34 | API key          |
| `RULE34_USER_ID`    | Rule34 | User ID          |

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
