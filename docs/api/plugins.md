# Plugins API Reference

Documentation for all available plugins.

## Core Plugins

### Bunkr

::: megaloader.plugins.Bunkr
    options:
      show_root_heading: true
      heading_level: 3

### Cyberdrop

::: megaloader.plugins.Cyberdrop
    options:
      show_root_heading: true
      heading_level: 3

### GoFile

::: megaloader.plugins.Gofile
    options:
      show_root_heading: true
      heading_level: 3

### PixelDrain

::: megaloader.plugins.PixelDrain
    options:
      show_root_heading: true
      heading_level: 3

## Extended Plugins

### Pixiv

::: megaloader.plugins.Pixiv
    options:
      show_root_heading: true
      heading_level: 3

### Fanbox

::: megaloader.plugins.Fanbox
    options:
      show_root_heading: true
      heading_level: 3

### Rule34

::: megaloader.plugins.Rule34
    options:
      show_root_heading: true
      heading_level: 3

### Fapello

::: megaloader.plugins.Fapello
    options:
      show_root_heading: true
      heading_level: 3

### Thotslife

::: megaloader.plugins.Thotslife
    options:
      show_root_heading: true
      heading_level: 3

### ThothubTO

::: megaloader.plugins.ThothubTO
    options:
      show_root_heading: true
      heading_level: 3

### ThothubVIP

::: megaloader.plugins.ThothubVIP
    options:
      show_root_heading: true
      heading_level: 3

## Plugin Registry

### get_plugin_class

::: megaloader.plugins.get_plugin_class
    options:
      show_root_heading: false
      heading_level: 3

### PLUGIN_REGISTRY

The `PLUGIN_REGISTRY` dictionary maps domain patterns to plugin classes:

```python
from megaloader.plugins import PLUGIN_REGISTRY

# View all registered plugins
for domains, plugin_class in PLUGIN_REGISTRY.items():
    print(f"{plugin_class.__name__}: {domains}")
```

Example output:
```
Bunkr: ('bunkr.si', 'bunkr.la', 'bunkr.is', 'bunkr.ru', 'bunkr.su', 'bunkr')
Cyberdrop: ('cyberdrop.me', 'cyberdrop.to', 'cyberdrop')
PixelDrain: pixeldrain.com
GoFile: gofile.io
...
```

## Usage Examples

### Using Core Plugins

```python
from megaloader import Bunkr, Cyberdrop, PixelDrain

# Bunkr album
bunkr = Bunkr("https://bunkr.si/a/example")
items = list(bunkr.export())

# Cyberdrop album
cyber = Cyberdrop("https://cyberdrop.me/a/example")
items = list(cyber.export())

# PixelDrain list
pixel = PixelDrain("https://pixeldrain.com/l/example")
items = list(pixel.export())
```

### Using Extended Plugins

```python
from megaloader.plugins import Pixiv, Fanbox

# Pixiv artwork (requires auth in .env)
pixiv = Pixiv("https://pixiv.net/artworks/12345")
items = list(pixiv.export())

# Fanbox creator (requires auth in .env)
fanbox = Fanbox("https://creator.fanbox.cc")
items = list(fanbox.export())
```

### Automatic Plugin Detection

```python
from megaloader.plugins import get_plugin_class

url = "https://bunkr.si/a/example"
plugin_class = get_plugin_class(url)

if plugin_class:
    print(f"Detected: {plugin_class.__name__}")
    plugin = plugin_class(url)
else:
    print("No plugin found for URL")
```

## See Also

- [Plugin System Guide](../guide/plugins.md)
- [Creating Custom Plugins](../development/creating-plugins.md)
- [Core API Reference](core.md)
