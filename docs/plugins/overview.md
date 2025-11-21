# Plugin System Overview

Megaloader uses a plugin-based architecture to support multiple file hosting platforms through a unified interface. Each platform is implemented as a separate plugin that inherits from the `BasePlugin` abstract class.

## How Plugins Work

When you call `extract(url)`, Megaloader automatically:

1. **Parses the domain** from the URL
2. **Looks up the plugin** in the plugin registry
3. **Instantiates the plugin** with your URL and options
4. **Yields items** as the plugin discovers them

This happens transparently—you don't need to know which plugin is being used.

## Plugin Architecture

### BasePlugin Abstract Class

All plugins inherit from `BasePlugin`, which provides:

- **Session management** with automatic retry logic for transient failures
- **Default headers** (User-Agent) for HTTP requests
- **Credential handling** convention (kwargs → environment variables)
- **Lazy evaluation** through generator-based extraction

### Required Implementation

Each plugin must implement:

```python
def extract(self) -> Generator[DownloadItem, None, None]:
    """Extract downloadable items from the URL."""
```

This method yields `DownloadItem` objects as files are discovered, enabling lazy evaluation and memory-efficient processing of large collections.

### Optional Customization

Plugins can override:

```python
def _configure_session(self, session: requests.Session) -> None:
    """Add plugin-specific headers, cookies, or authentication."""
```

This method is called once when the session is first created, allowing plugins to add platform-specific requirements like Referer headers or authentication tokens.

## Domain Resolution

The plugin system uses a three-tier resolution strategy:

### 1. Exact Match

The most common case—direct domain lookup:

```python
# "pixeldrain.com" → PixelDrain plugin
# "gofile.io" → Gofile plugin
```

### 2. Subdomain Support

Some platforms use creator-specific subdomains:

```python
# "creator.fanbox.cc" → Fanbox plugin
# "artist.fanbox.cc" → Fanbox plugin
```

Domains in the `SUBDOMAIN_SUPPORTED` set are matched by their base domain.

### 3. Partial Match (Fallback)

For domain variations and www prefixes:

```python
# "www.pixiv.net" → Pixiv plugin
# "en.pixiv.net" → Pixiv plugin
```

This fallback ensures compatibility with domain variations without explicit registration.

## Plugin Lifecycle

Here's what happens when you extract from a URL:

```python
import megaloader as mgl

for item in mgl.extract("https://pixeldrain.com/l/abc123"):
    print(item.filename)
```

**Step-by-step:**

1. **URL Validation**: The URL is parsed and validated
2. **Domain Extraction**: `pixeldrain.com` is extracted from the URL
3. **Plugin Lookup**: `get_plugin_class("pixeldrain.com")` returns `PixelDrain`
4. **Plugin Initialization**: `PixelDrain(url)` is instantiated
5. **Session Creation**: On first use, a session is created with retry logic
6. **Session Configuration**: `_configure_session()` adds plugin-specific headers
7. **Extraction**: `extract()` method yields items as they're discovered
8. **Item Yielding**: Each `DownloadItem` is yielded to the caller

## Plugin Registry

The `PLUGIN_REGISTRY` dictionary maps domains to plugin classes:

```python
PLUGIN_REGISTRY = {
    "bunkr.si": Bunkr,
    "bunkr.la": Bunkr,
    "pixeldrain.com": PixelDrain,
    "gofile.io": Gofile,
    # ... more domains
}
```

Multiple domains can map to the same plugin class (e.g., Bunkr has multiple domain variations).

## Error Handling

The plugin system raises specific exceptions:

- **`UnsupportedDomainError`**: No plugin found for the domain
- **`ExtractionError`**: Network or parsing failure during extraction
- **`ValueError`**: Invalid URL format or missing required parameters

Plugins should let network errors propagate naturally—the `extract()` function wraps them in `ExtractionError` automatically.

## Next Steps

- [Supported Platforms](./supported-platforms.md) - See all available plugins
- [Plugin Options](./plugin-options.md) - Learn about platform-specific parameters
- [Creating Plugins](./creating-plugins.md) - Build your own plugin
