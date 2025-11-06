# Megaloader Documentation

Welcome to the Megaloader documentation! This project will make you smile. 😊

Megaloader is a Python library that automatically downloads content from
multiple file hosting and media platforms using a plugin-based architecture.

## Features

- **Automatic Detection**: Just provide a URL, and Megaloader automatically
  selects the right plugin
- **Multi-Platform**: Support for 11+ platforms including Bunkr, Cyberdrop,
  GoFile, PixelDrain, and more
- **Plugin Architecture**: Easy to extend with new platforms
- **CLI Tool**: Command-line interface for quick downloads
- **Type-Safe**: Full type hints and mypy compliance

## Quick Example

```python
from megaloader import download

# Automatic plugin detection
download("https://pixeldrain.com/u/95u1wnsd", "./downloads")
download("https://cyberdrop.me/a/0OpiyaOV", "./downloads")
```

## Supported Platforms

| Platform    | Domain(s)                  | Status      |
| ----------- | -------------------------- | ----------- |
| Bunkr       | bunkr._, bunkrr._          | ✅ Core     |
| Cyberdrop   | cyberdrop.\*               | ✅ Core     |
| GoFile      | gofile.io                  | ✅ Core     |
| PixelDrain  | pixeldrain.com             | ✅ Core     |
| Pixiv       | pixiv.net                  | ⚠️ Extended |
| Rule34      | rule34.xxx                 | ⚠️ Extended |
| Fanbox      | fanbox.cc                  | ⚠️ Extended |
| Fapello     | fapello.com                | ⚠️ Extended |
| Thotslife   | thotslife.com              | ⚠️ Extended |
| Thothub.to  | thothub.to                 | ⚠️ Extended |
| Thothub.vip | thothub.vip, thothub.today | ⚠️ Extended |

## Try It Out

Test URL compatibility with our plugins:

<script setup>
import DemoComponent from './Demo.vue'
</script>

<DemoComponent />

## Getting Started

Check out the [Installation Guide](getting-started/installation.md) to get
started, or jump straight to the [Quick Start](getting-started/quickstart.md)
for examples.

## Components

This monorepo contains:

- **Core Library** (`packages/megaloader`): The main download library
- **CLI Tool** (`packages/cli`): Command-line interface
- **API** (`api/`): FastAPI server for development and Vercel deployment

## Links

- [GitHub Repository](https://github.com/totallynotdavid/megaloader)
- [Issue Tracker](https://github.com/totallynotdavid/megaloader/issues)
- [PyPI Package](https://pypi.org/project/megaloader/)
