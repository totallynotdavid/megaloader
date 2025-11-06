# Core API Reference

::: megaloader
    options:
      show_root_heading: true
      show_source: true
      heading_level: 2

## Main Functions

### download

::: megaloader.download
    options:
      show_root_heading: false
      heading_level: 3

## Base Classes

### BasePlugin

::: megaloader.plugin.BasePlugin
    options:
      show_root_heading: false
      heading_level: 3
      members:
        - __init__
        - export
        - download_file

### Item

::: megaloader.plugin.Item
    options:
      show_root_heading: false
      heading_level: 3

## HTTP Utilities

### HTTP Functions

::: megaloader.http
    options:
      show_root_heading: false
      heading_level: 3
      filters:
        - "!^_"

## Exceptions

::: megaloader.exceptions
    options:
      show_root_heading: false
      heading_level: 3

## Usage Examples

### Basic Download

```python
from megaloader import download

# Simple download with auto-detection
success = download("https://pixeldrain.com/u/file_id", "./downloads")

if success:
    print("Download completed successfully")
```

### Using Specific Plugin

```python
from megaloader import download, Bunkr

# Force specific plugin
success = download(
    "https://custom-domain.com/file",
    "./downloads",
    plugin_class=Bunkr
)
```

### Direct Plugin Usage

```python
from megaloader.plugins import Cyberdrop

# Initialize plugin
plugin = Cyberdrop("https://cyberdrop.me/a/album")

# Export items
items = list(plugin.export())

# Download each item
for item in items:
    success = plugin.download_file(item, "./downloads")
    print(f"{item.filename}: {'✓' if success else '✗'}")
```

### Working with Items

```python
from megaloader.plugin import Item
from megaloader.plugins import PixelDrain

plugin = PixelDrain("https://pixeldrain.com/l/list_id")

for item in plugin.export():
    print(f"URL: {item.url}")
    print(f"Filename: {item.filename}")
    print(f"Album: {item.album_title}")
    print(f"File ID: {item.file_id}")
    print(f"Metadata: {item.metadata}")
```

## Type Hints

All functions and classes include full type hints for IDE support:

```python
from typing import Generator
from megaloader.plugin import BasePlugin, Item

def process_plugin(plugin: BasePlugin) -> list[Item]:
    """Process plugin and return items."""
    return list(plugin.export())
```
