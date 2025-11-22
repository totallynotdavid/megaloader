---
title: User guide overview
description: Learn about megaloader's core library, generator-based API, and plugin architecture for extracting file metadata from hosting platforms.
outline: [2, 3]
prev:
  text: 'Quick start'
  link: '/getting-started/quickstart'
next:
  text: 'Basic usage'
  link: '/guide/basic-usage'
---

# User guide overview

The megaloader core library is a Python package for extracting downloadable content metadata from file hosting platforms. It provides a clean, generator-based API that separates metadata extraction from the actual downloading process.

## What megaloader does

Megaloader **extracts metadata** about downloadable files:

- Direct download URLs
- Original filenames
- File sizes (when available)
- Collection/album names
- Required HTTP headers for authentication

Megaloader **does not** download files. It gives you the information you need to implement downloads however you want.

## Why separate extraction from downloading?

This separation provides several benefits:

**Flexibility**: You control how files are downloaded. Use any HTTP library, implement custom retry logic, add progress bars, or integrate with existing download managers.

**Efficiency**: Extract metadata once, then decide what to download. Filter by filename, size, or collection before downloading anything.

**Simplicity**: The library focuses on one thing—parsing platform-specific pages and APIs to find downloadable content. Download implementation is straightforward HTTP requests.

**Testability**: Extraction logic can be tested without actually downloading gigabytes of files.

## Generator-based API

The core `extract()` function returns a generator that yields items lazily:

```python
import megaloader as mgl

# Returns immediately - no network requests yet
items = mgl.extract("https://pixeldrain.com/l/abc123")

# Network requests happen during iteration
for item in items:
    print(item.filename)  # Discovered as we iterate
```

### Benefits of lazy evaluation

**Memory efficient**: Process thousands of files without loading all metadata into memory at once.

**Fast startup**: Start processing the first items immediately while later pages are still loading.

**Early termination**: Stop iteration early if you find what you need—no wasted requests.

**Natural streaming**: Perfect for pipelines, progress bars, and real-time processing.

## Basic usage pattern

The typical workflow is simple:

1. **Extract metadata** using `extract()`
2. **Iterate over items** to access metadata
3. **Download files** using the metadata

```python
import megaloader as mgl
import requests

# Step 1: Extract metadata
for item in mgl.extract(url):
    # Step 2: Access metadata
    print(f"Found: {item.filename} ({item.size_bytes} bytes)")
    
    # Step 3: Download the file
    response = requests.get(item.download_url, headers=item.headers)
    with open(item.filename, 'wb') as f:
        f.write(response.content)
```

## Plugin architecture

Megaloader uses a plugin system to support different platforms. Each platform has a dedicated plugin that knows how to:

- Parse that platform's page structure
- Handle authentication and rate limiting
- Extract download URLs and metadata

The `extract()` function automatically selects the right plugin based on the URL domain:

```python
# Automatically uses PixelDrain plugin
mgl.extract("https://pixeldrain.com/l/abc123")

# Automatically uses Gofile plugin
mgl.extract("https://gofile.io/d/xyz789")
```

You don't need to know which plugin is used—the API is consistent across all platforms.

## Supported platforms

Megaloader currently supports 11 platforms across two tiers:

**Core Platforms** (actively maintained):
- Bunkr (multiple domains)
- PixelDrain
- Cyberdrop (multiple domains)
- GoFile

**Extended Platforms** (best-effort support):
- Fanbox
- Pixiv
- Rule34
- ThotsLife
- ThotHub (TO and VIP variants)
- Fapello

See [supported platforms](/plugins/supported-platforms) for the complete list of domains.

## When to use megaloader

Megaloader is ideal when you need to:

- Extract file lists from galleries or albums
- Build custom download workflows
- Filter content before downloading
- Integrate file hosting platforms into your application
- Archive or backup content from supported platforms

## When not to use megaloader

Megaloader might not be the right choice if you:

- Need a complete download manager (use the CLI tool instead)
- Only work with platforms that aren't supported
- Need real-time streaming (Megaloader is for discrete files)
- Want a GUI application (Megaloader is a library/CLI tool)
