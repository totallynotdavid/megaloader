# Using the library

Megaloader is built around a few simple ideas: lazy evaluation, platform
plugins, and separation between extraction and downloading.

## Generator-based extraction

`extract()` returns a generator, not a list:

```python
import megaloader as mgl

# This returns immediately. No network requests yet
items = mgl.extract("https://pixeldrain.com/l/DDGtvvTU")

for item in items:
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

Requests happen during iteration. This lets you process early files while later
pages load, which matters for galleries with thousands of items.

To count items or iterate multiple times, materialize the generator:

```python
items = list(mgl.extract("https://pixeldrain.com/l/DDGtvvTU"))
print(f"Found {len(items)} files")
```

::: details Output

```
Found 6 files
```

:::

This loads all metadata into memory at once.

## DownloadItem structure

Every file is represented by a `DownloadItem`:

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

The required fields are `download_url` and `filename`. Everything else provides
context:

```python
for item in mgl.extract("https://gofile.io/d/wUbPe1"):
    print(f"{item.filename} - {item.size_bytes} bytes")
    if item.collection_name:
        print(f"  Collection: {item.collection_name}")
```

::: details Output

```
sample-image-05.jpg - 202748 bytes
  Collection: images
sample-image-06.jpg - 89101 bytes
  Collection: images
sample-image-04.jpg - 412156 bytes
  Collection: images
sample-image-03.jpg - 286359 bytes
  Collection: images
sample-image-01.jpg - 207558 bytes
  Collection: images
sample-image-02.jpg - 405661 bytes
  Collection: images
```

:::

Always include `item.headers` in your download requests. Some platforms require
specific headers to access files, and omitting them can lead to errors such as
HTTP 403 or 502. Currently, Bunkr, Thothub and Pixiv require headers.

If a platform requires headers, they will be included in `item.headers`. Make
sure to merge them into your download requests.

## Plugin architecture

Each platform has a plugin that handles parsing. When you call `extract()`:

1. The domain is extracted from your URL
2. The appropriate plugin is looked up in `PLUGIN_REGISTRY`
3. The plugin is instantiated with your URL and options
4. The plugin's generator is returned

You rarely need to interact with plugins directly, but you can:

```python
from megaloader.plugins import PixelDrain

plugin = PixelDrain("https://pixeldrain.com/l/abc123")

for item in plugin.extract():
    print(item.filename)
```

This is useful when you want to reuse a plugin instance or when a new domain
pattern isn't yet recognized by `extract()`.

Plugins inherit from `BasePlugin`, which provides session management, retry
logic, and default headers automatically.

Check if a domain is supported:

```python
from megaloader.plugins import get_plugin_class

if get_plugin_class("pixeldrain.com"):
    print("pixeldrain.com is supported!")
```

Megaloader supports 11 platforms split into core (Bunkr, PixelDrain, Cyberdrop,
GoFile) and extended (Fanbox, Pixiv, Rule34, etc) tiers. See the
[platforms reference](../reference/platforms) for the complete list.

## Platform-specific options

Some platforms accept parameters. GoFile supports password-protected folders:

```python
mgl.extract("https://gofile.io/d/abc123", password="secret")
```

Fanbox and Pixiv often require session cookies:

```python
mgl.extract("https://creator.fanbox.cc", session_id="your_cookie")
```

Rule34 supports API credentials:

```python
mgl.extract("https://rule34.xxx/...", api_key="key", user_id="id")
```

Most plugins support environment variables as fallback:

```python
import os

os.environ["FANBOX_SESSION_ID"] = "your_cookie"
mgl.extract("https://creator.fanbox.cc")
```

Explicit kwargs take precedence over environment variables. Check
[plugin options](/reference/options) for details.

## Error handling

Three exceptions cover most error cases:

`ValueError` for malformed or empty URLs:

```python
try:
    mgl.extract("")
except ValueError as e:
    print(f"ValueError: {e}")
```

::: details Output

```
ValueError: URL cannot be empty
```

:::

`UnsupportedDomainError` when no plugin exists for the domain:

```python
try:
    mgl.extract("https://unknown-site.com/file")
except mgl.UnsupportedDomainError as e:
    print(f"Platform '{e.domain}' not supported")
```

::: details Output

```
Platform 'random-site.com' not supported
```

:::

`ExtractionError` for network or parsing failures:

```python
try:
    items = list(mgl.extract(url))
except mgl.ExtractionError as e:
    print(f"Failed: {e}")
```

`ExtractionError` covers network timeouts, authentication failures, broken URLs,
and platform changes that broke the plugin. The exception message usually
indicates what went wrong.

## Working with collections

Many platforms organize files into albums or galleries. The `collection_name`
field lets you recreate this structure:

```python
from collections import defaultdict

collections = defaultdict(list)

for item in mgl.extract(url):
    name = item.collection_name or "uncategorized"
    collections[name].append(item)

for collection, items in collections.items():
    print(f"{collection}: {len(items)} files")
```

This is useful for maintaining album structure when downloading.

## Filtering during extraction

Since `extract()` returns a generator, you can filter items as they're
discovered. Below are common patterns:

Filter by file extension:

```python
# Only images
for item in mgl.extract(url):
    if item.filename.lower().endswith(('.jpg', '.png', '.webp')):
        process_image(item)
```

Filter by file size:

```python
# Only files larger than 1 MB
for item in mgl.extract(url):
    if item.size_bytes and item.size_bytes > 1_000_000:
        process_large_file(item)
```

Stop early to avoid unnecesary network requests:

```python
# Stop after finding 10 items
count = 0
for item in mgl.extract(url):
    count += 1
    if count >= 10:
        break
```

Breaking early prevents later network requests from happening, which is a
benefit of lazy evaluation.

## Why separate extraction from downloads

This separation provides full control over downloads. Use any HTTP library,
implement custom retry logic, add progress bars, handle concurrency however you
want. Extract once, filter what you need, download only those files. The library
focuses on the hard part: parsing platform-specific formats and finding download
URLs.
