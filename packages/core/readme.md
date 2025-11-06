# Megaloader Core Library

This is the core library for Megaloader, providing a plugin-based architecture
for downloading content from various file hosting and media platforms.

## Installation

```bash
uv pip install megaloader
```

## Basic Usage

```python
from megaloader import download

# Automatic plugin detection
download("https://pixeldrain.com/u/95u1wnsd", "./downloads")
download("https://cyberdrop.me/a/0OpiyaOV", "./downloads")
```

## Advanced Usage

```python
from megaloader import Bunkr

# Use specific plugin
download(
    "https://bunkrr.su/d/example.zip",
    "./downloads",
    plugin_class=Bunkr,
)
```

For full documentation, see the [main repository](../../README.md).
