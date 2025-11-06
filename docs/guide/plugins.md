# Plugin System

Megaloader uses a plugin-based architecture to support multiple platforms.

## How Plugins Work

Each plugin extends the `BasePlugin` class and implements:

- `export()`: Extracts downloadable items from URLs
- `download_file()`: Downloads a single item

## Available Plugins

### Core Plugins (Actively Maintained)

#### Bunkr

- **Domains**: bunkr.si, bunkr.la, bunkr.is, bunkr.ru, bunkr.su
- **Supports**: Albums, single files
- **Features**: Multiple domain mirrors

```python
from megaloader import Bunkr

plugin = Bunkr("https://bunkr.si/a/example")
items = list(plugin.export())
```

#### PixelDrain

- **Domain**: pixeldrain.com
- **Supports**: Lists, single files
- **Features**: Proxy support

```python
from megaloader import PixelDrain

plugin = PixelDrain("https://pixeldrain.com/l/list_id")
# Enable proxy
download(url, "./downloads", plugin_class=PixelDrain, use_proxy=True)
```

#### Cyberdrop

- **Domains**: cyberdrop.me, cyberdrop.to
- **Supports**: Albums, single files

```python
from megaloader import Cyberdrop

plugin = Cyberdrop("https://cyberdrop.me/a/album_id")
```

#### GoFile

- **Domain**: gofile.io
- **Supports**: Folders (including password-protected), single files
- **Features**: Password support via environment variables

```python
from megaloader import Gofile

# For password-protected folders, set GOFILE_PASSWORD in .env
plugin = Gofile("https://gofile.io/d/folder_id")
```

### Extended Plugins (Best Effort)

These plugins work but may break without immediate fixes:

- **Pixiv**: Artwork galleries, requires authentication
- **Fanbox**: Creator content, requires authentication
- **Rule34**: Tags and posts
- **Thotslife**: Albums and blog posts
- **Thothub.vip**: Videos and albums
- **Thothub.to**: Videos and albums
- **Fapello**: Model profiles

## Plugin Detection

Megaloader automatically detects the right plugin:

```python
from megaloader import download

# Automatically uses Bunkr plugin
download("https://bunkr.si/a/example", "./downloads")

# Automatically uses PixelDrain plugin
download("https://pixeldrain.com/u/file", "./downloads")
```

## Manual Plugin Selection

Force a specific plugin when needed:

```python
from megaloader import download, Bunkr

# Useful if domain changes or for custom mirrors
download(
    "https://custom-bunkr-mirror.com/a/example",
    "./downloads",
    plugin_class=Bunkr
)
```

## Plugin Configuration

### Environment Variables

Some plugins require configuration via `.env`:

```bash
# GoFile password-protected folders
GOFILE_PASSWORD=your_password

# Pixiv authentication
PIXIV_REFRESH_TOKEN=your_token

# Fanbox authentication
FANBOX_SESSION_ID=your_session

# Rule34 API (optional)
RULE34_API_KEY=your_key
```

### Proxy Support

Enable proxy for specific plugins:

```python
from megaloader import download, PixelDrain

download(
    "https://pixeldrain.com/u/file",
    "./downloads",
    plugin_class=PixelDrain,
    use_proxy=True
)
```

## Plugin Registry

View all registered plugins:

```python
from megaloader.plugins import PLUGIN_REGISTRY

for domains, plugin_class in PLUGIN_REGISTRY.items():
    print(f"{plugin_class.__name__}: {domains}")
```

Or use the CLI:

```bash
megaloader list-plugins
```

## Creating Custom Plugins

See [Creating Plugins](../development/creating-plugins.md) for how to create
your own plugins.

## Plugin Lifecycle

1. **URL Detection**: Registry matches URL to plugin
2. **Initialization**: Plugin parses URL structure
3. **Export**: Plugin extracts downloadable items
4. **Download**: Each item is downloaded individually

## Plugin Options

Common options across plugins:

```python
from megaloader import download

download(
    url,
    "./downloads",
    plugin_class=None,           # Auto-detect or specify
    use_proxy=False,             # Enable proxy
    create_album_subdirs=True,   # Create album folders
)
```

## Next Steps

- [Advanced Usage](advanced-usage.md)
- [Creating Plugins](../development/creating-plugins.md)
- [API Reference](../api/plugins.md)
