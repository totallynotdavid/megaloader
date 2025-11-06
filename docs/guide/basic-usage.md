# Basic Usage

Learn how to use Megaloader for common download tasks.

## Simple Downloads

The `download()` function handles most use cases:

```python
from megaloader import download

# Single file download
success = download("https://pixeldrain.com/u/95u1wnsd", "./downloads")
if success:
    print("Download completed!")
```

## Album Downloads

For platforms that support albums (collections):

```python
from megaloader import download

# Download entire album
download("https://cyberdrop.me/a/0OpiyaOV", "./downloads")

# Files will be organized in subdirectories by album name
```

## Disable Subdirectories

By default, albums create subdirectories. To disable:

```python
download(
    "https://cyberdrop.me/a/album",
    "./downloads",
    create_album_subdirs=False
)
```

## Using Specific Plugins

If automatic detection fails or you want to force a specific plugin:

```python
from megaloader import download, Bunkr, PixelDrain

# Force Bunkr plugin
download(
    "https://custom-domain.com/file",
    "./downloads",
    plugin_class=Bunkr
)

# Force PixelDrain plugin
download(
    "https://mirror.com/file",
    "./downloads",
    plugin_class=PixelDrain
)
```

## Error Handling

Handle download failures gracefully:

```python
from megaloader import download

try:
    success = download(url, "./downloads")
    if not success:
        print("Download failed")
except Exception as e:
    print(f"Error: {e}")
```

## Logging

Enable logging to see what's happening:

```python
import logging

# Enable INFO level logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(name)s: %(message)s"
)

from megaloader import download

download("https://example.com/file", "./downloads")
```

Debug level for more details:

```python
logging.basicConfig(level=logging.DEBUG)
```

## Next Steps

- [Advanced Usage](advanced-usage.md)
- [Plugin System](plugins.md)
- [API Reference](../api/core.md)
