# Advanced Usage

Learn advanced techniques for using Megaloader.

## Direct Plugin Usage

For fine-grained control, use plugin classes directly:

```python
from megaloader.plugins import Cyberdrop

# Initialize plugin
plugin = Cyberdrop("https://cyberdrop.me/a/album_id")

# Extract all items first for progress tracking
items = list(plugin.export())
print(f"Found {len(items)} files to download")

# Download with custom logic
for i, item in enumerate(items):
    print(f"Downloading {i+1}/{len(items)}: {item.filename}")
    success = plugin.download_file(item, "./downloads/")
    if not success:
        print(f"Failed to download {item.filename}")
```

## Custom HTTP Sessions

Create custom sessions with retry logic, proxies, or custom headers:

```python
import requests
from megaloader.plugins import Bunkr

# Note: Current implementation creates internal sessions
# This is a placeholder for future custom session support

# Create session with retry logic
session = requests.Session()
adapter = requests.adapters.HTTPAdapter(max_retries=3)
session.mount('http://', adapter)
session.mount('https://', adapter)

# Future: Pass session to plugin
# plugin = Bunkr(url, session=session)
```

## Batch Processing

Process multiple URLs efficiently:

```python
from megaloader import download
from concurrent.futures import ThreadPoolExecutor

urls = [
    "https://pixeldrain.com/u/file1",
    "https://cyberdrop.me/a/album1",
    "https://bunkr.si/a/example",
]

def download_url(url):
    try:
        success = download(url, "./downloads")
        return (url, success)
    except Exception as e:
        return (url, False, str(e))

# Download concurrently (be mindful of rate limits)
with ThreadPoolExecutor(max_workers=3) as executor:
    results = list(executor.map(download_url, urls))

for result in results:
    url = result[0]
    success = result[1]
    print(f"{url}: {'✓' if success else '✗'}")
```

## Progress Tracking

Track download progress for better UX:

```python
from megaloader.plugins import GoFile

plugin = GoFile("https://gofile.io/d/example")
items = list(plugin.export())

print(f"Downloading {len(items)} files...")

successful = 0
failed = 0

for i, item in enumerate(items, 1):
    print(f"[{i}/{len(items)}] {item.filename}... ", end="")
    
    if plugin.download_file(item, "./downloads"):
        print("✓")
        successful += 1
    else:
        print("✗")
        failed += 1

print(f"\nCompleted: {successful} successful, {failed} failed")
```

## Custom Output Organization

Organize downloads with custom naming:

```python
from pathlib import Path
from megaloader.plugins import PixelDrain

plugin = PixelDrain("https://pixeldrain.com/l/list_id")

for item in plugin.export():
    # Create custom subdirectory structure
    if item.album_title:
        output_dir = Path("./downloads") / item.album_title
    else:
        output_dir = Path("./downloads/misc")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Add custom prefix to filename
    custom_filename = f"pixeldrain_{item.filename}"
    
    # Download would need custom implementation
    # This is a concept example
    plugin.download_file(item, str(output_dir))
```

## Error Handling

Robust error handling for production use:

```python
import logging
from megaloader import download
from megaloader.exceptions import DownloadError

logging.basicConfig(level=logging.INFO)

def safe_download(url, output_dir, max_retries=3):
    """Download with retry logic."""
    for attempt in range(max_retries):
        try:
            success = download(url, output_dir)
            if success:
                return True
            logging.warning(f"Attempt {attempt + 1} failed for {url}")
        except Exception as e:
            logging.error(f"Error on attempt {attempt + 1}: {e}")
            if attempt == max_retries - 1:
                raise
    return False

# Use it
try:
    safe_download("https://example.com/file", "./downloads")
except Exception as e:
    logging.critical(f"Download failed after all retries: {e}")
```

## Working with Metadata

Access and use item metadata:

```python
from megaloader.plugins import Cyberdrop

plugin = Cyberdrop("https://cyberdrop.me/a/example")

for item in plugin.export():
    print(f"File: {item.filename}")
    print(f"URL: {item.url}")
    print(f"Album: {item.album_title}")
    print(f"ID: {item.file_id}")
    
    if item.metadata:
        print(f"Metadata: {item.metadata}")
    
    print("---")
```

## Next Steps

- [Plugin System](plugins.md)
- [API Reference](../api/core.md)
- [Creating Plugins](../development/creating-plugins.md)
