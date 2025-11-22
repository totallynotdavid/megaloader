# Basic usage

Megaloader is built around a few simple ideas: lazy evaluation through
generators, platform-specific plugins, and clean separation between extraction
and downloading.

## Generator-based extraction

The `extract()` function returns a generator, not a list:

```python
import megaloader as mgl

# This returns immediately. No network requests yet
items = mgl.extract("https://pixeldrain.com/l/DDGtvvTU")

# Requests happen during iteration
for item in items:
    print(item.filename)  # Discovered as we go
```

This yields each file as it's discovered:

```
sample-image-01.jpg
sample-image-02.jpg
sample-image-03.jpg
sample-image-04.jpg
sample-image-05.jpg
sample-image-06.jpg
```

This lazy evaluation means you can start processing the first files while later
pages are still loading. For large galleries with thousands of files, this can
make a difference.

If you actually need a list (to count items, iterate multiple times, etc), just
materialize the generator:

```python
items = list(mgl.extract("https://pixeldrain.com/l/DDGtvvTU"))
print(f"Found {len(items)} files")
```

Output:

```
Found 6 files
```

Keep in mind this loads all metadata into memory at once.

## The DownloadItem dataclass

Every file is represented by a `DownloadItem` with these fields:

```python
@dataclass
class DownloadItem:
    download_url: str                    # Required
    filename: str                        # Required
    collection_name: str | None = None   # Optional grouping
    source_id: str | None = None         # Platform ID
    headers: dict[str, str] = field(default_factory=dict)
    size_bytes: int | None = None
```

The two required fields are `download_url` and `filename`, which are everything
you need to download a file. The rest provides context:

```python
for item in mgl.extract("https://pixeldrain.com/l/DDGtvvTU"):
    print(f"Filename: {item.filename}")

    if item.size_bytes:
        mb = item.size_bytes / 1_000_000
        print(f"Size: {mb:.2f} MB")
```

Example output:

```
Filename: sample-image-01.jpg
Size: 0.21 MB
Filename: sample-image-02.jpg
Size: 0.19 MB
Filename: sample-image-03.jpg
Size: 0.20 MB
```

Always use `item.headers` in your download requests. Some platforms require
things like `Referer` headers to prevent hotlinking.

## Plugin architecture

Under the hood, Megaloader uses a plugin system. Each platform has a plugin that
knows how to parse that platform's pages and APIs. When you call `extract()`,
the library:

1. Parses the domain from your URL
2. Looks up the appropriate plugin
3. Instantiates it with your URL and options
4. Returns the plugin's generator

You normally do not need to interact with plugins directly because `extract()`
handles that for you. You can still do it manually if you want:

```python
from megaloader.plugins import PixelDrain

plugin = PixelDrain("https://pixeldrain.com/l/abc123")

for item in plugin.extract():
    print(item.filename)
```

This can be useful if you want to reuse the same plugin instance, or if a
platform adds a new domain or URL pattern that is not yet recognized by
`extract()`.

### Platform support

Megaloader currently supports 11 platforms split into two tiers. Core platforms
(Bunkr, PixelDrain, Cyberdrop, GoFile) get active maintenance. Extended
platforms (Fanbox, Pixiv, Rule34, etc) work but receive best-effort support.

To check if a domain is supported:

```python
from megaloader.plugins import get_plugin_class

if get_plugin_class("pixeldrain.com"):
    print("pixeldrain.com is supported!")
```

Output:

```
pixeldrain.com is supported!
```

See the [platforms page](/reference/plugin-platforms) for the complete list.

## Platform-specific options

Some platforms need extra parameters. You can pass these as keyword arguments to
`extract()`.

For example, GoFile folders may be password-protected:

```python
mgl.extract("https://gofile.io/d/abc123", password="secret")
```

Fanbox and Pixiv often require a session cookie for authentication:

```python
mgl.extract("https://creator.fanbox.cc", session_id="your_cookie")
```

Rule34 supports API credentials:

```python
mgl.extract("https://rule34.xxx/...", api_key="key", user_id="id")
```

Most plugins also support environment variables as fallback credentials:

```python
import os

os.environ["FANBOX_SESSION_ID"] = "your_cookie"
mgl.extract("https://creator.fanbox.cc")  # Uses env var
```

Explicit kwargs always take precedence over environment variables. Check
[plugin options](/reference/plugin-options) for what each platform supports.

## Error handling

Three exceptions you'll encounter:

**`ValueError`** for malformed URLs:

```python
try:
    mgl.extract("")  # Empty URL
except ValueError as e:
    print(f"ValueError: {e}")
```

Output:

```
ValueError: URL cannot be empty
```

**`UnsupportedDomainError`** when the platform isn't supported:

```python
try:
    mgl.extract("https://random-site.com/file")
except mgl.UnsupportedDomainError as e:
    print(f"Platform '{e.domain}' not supported")
```

Output:

```
Platform 'random-site.com' not supported
```

**`ExtractionError`** for network or parsing failures:

```python
try:
    items = list(mgl.extract(url))
except mgl.ExtractionError as e:
    print(f"Failed: {e}")
```

`ExtractionError` covers a range of issues: network timeouts, authentication
failures, broken URLs, platform changes that broke the plugin, etc. The
exception message usually gives you a hint about what went wrong.

## Working with collections

Many platforms organize files into collections (albums, galleries, user pages).
The `collection_name` field lets you recreate this structure:

```python
from collections import defaultdict

collections = defaultdict(list)

for item in mgl.extract(url):
    name = item.collection_name or "uncategorized"
    collections[name].append(item)

for collection, items in collections.items():
    print(f"{collection}: {len(items)} files")
```

This is particularly useful for maintaining album structure when downloading.

## Filtering during extraction

Since `extract()` returns a generator, you can filter items as they're
discovered without loading everything into memory:

```python
# Only images
for item in mgl.extract(url):
    if item.filename.lower().endswith(('.jpg', '.png', '.webp')):
        # Process image
        pass

# Only files larger than 1MB
for item in mgl.extract(url):
    if item.size_bytes and item.size_bytes > 1_000_000:
        # Process large file
        pass

# Stop after finding 10 items
count = 0
for item in mgl.extract(url):
    count += 1
    if count >= 10:
        break
```

Breaking out of the loop early means later network requests never happen, which
is one of the benefits of lazy evaluation.

## Why separate extraction from downloads?

This might seem unusual if you're used to libraries (like gallery-dl) that
handle everything. The separation provides several advantages:

**Full control**: Use any HTTP library, implement custom retry logic, add
progress bars, handle concurrency however you want. Deploy and use it wherever
you want.

**Efficiency**: Extract once, filter what you need, then download only those
files. No wasted bandwidth.

**Testability**: I can test the extraction logic without actually downloading
many of files. 😮‍💨

**Integration**: Easy to integrate with existing download managers, job queues,
or processing pipelines.

The library focuses on the hard part: parsing platform-specific formats and
finding download URLs. Downloading is just standard HTTP requests that you
implement however makes sense for your use case.
