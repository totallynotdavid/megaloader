# Quick Start

Get started with Megaloader in minutes!

## Basic Download

The simplest way to use Megaloader is with the `download()` function:

```python
from megaloader import download

# Download a single file
download("https://pixeldrain.com/u/95u1wnsd", "./downloads")

# Download an album
download("https://cyberdrop.me/a/0OpiyaOV", "./downloads")
```

## Using the CLI

If you installed the CLI package:

```bash
megaloader download-url "https://pixeldrain.com/u/95u1wnsd" ./downloads
```

## Specify a Plugin

For more control, specify the plugin directly:

```python
from megaloader import download, Bunkr

download(
    "https://bunkrr.su/d/example.zip",
    "./downloads",
    plugin_class=Bunkr,
)
```

## Advanced Usage

Use plugins directly for more control:

```python
from megaloader import PixelDrain

# Initialize plugin
plugin = PixelDrain("https://pixeldrain.com/l/nH4ZKt3b")

# Export all downloadable items
items = list(plugin.export())

# Download items manually
for item in items:
    success = plugin.download_file(item, "./downloads")
    if success:
        print(f"Downloaded: {item.filename}")
```

## Configuration Options

### Disable Subdirectories

```python
download(
    "https://cyberdrop.me/a/album",
    "./downloads",
    create_album_subdirs=False,  # Don't create album subdirectories
)
```

### Use Proxy

```python
from megaloader import download, PixelDrain

download(
    "https://pixeldrain.com/u/file",
    "./downloads",
    plugin_class=PixelDrain,
    use_proxy=True,  # Use proxy for downloads
)
```

## Enable Logging

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(name)s: %(message)s"
)

from megaloader import download

download("https://example.com/file", "./downloads")
```

## Next Steps

- [Basic Usage Guide](../guide/basic-usage.md)
- [Plugin System](../guide/plugins.md)
- [API Reference](../api/core.md)
