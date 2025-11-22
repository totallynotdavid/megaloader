---
title: Download implementation
description: Guide to implementing file downloads with streaming, progress bars, retry logic, and concurrent downloads.
outline: [2, 3]
prev:
  text: 'Basic usage'
  link: '/guide/basic-usage'
next:
  text: 'Advanced usage'
  link: '/guide/advanced-usage'
---

# Download implementation

Megaloader extracts metadata but doesn't download files. This guide shows you how to implement downloads using the extracted metadata.

[[toc]]

## Why separate downloads?

Separating extraction from downloading provides several advantages:

**Flexibility**: Choose your HTTP library, implement custom retry logic, add progress tracking, or integrate with existing download managers.

**Efficiency**: Extract once, filter what you want, then download only selected files.

**Control**: Implement rate limiting, concurrent downloads, resume logic, or any custom behavior.

**Simplicity**: Downloading is just HTTP GET requests—no complex logic needed.

## Simple download with requests

The most basic download implementation:

```python
import megaloader as mgl
import requests
from pathlib import Path

def download_item(item, output_dir: str = "./downloads"):
    """Download a single item."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    filepath = output_path / item.filename
    
    # Download with required headers
    response = requests.get(item.download_url, headers=item.headers)
    response.raise_for_status()
    
    # Save to disk
    with open(filepath, 'wb') as f:
        f.write(response.content)
    
    return filepath

# Usage
for item in mgl.extract("https://pixeldrain.com/l/abc123"):
    filepath = download_item(item)
    print(f"Downloaded: {filepath}")
```

## Streaming downloads

For large files, stream the download to avoid loading everything into memory:

```python
import megaloader as mgl
import requests
from pathlib import Path

def download_streaming(item, output_dir: str = "./downloads"):
    """Download with streaming for large files."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    filepath = output_path / item.filename
    
    # Stream download
    response = requests.get(
        item.download_url,
        headers=item.headers,
        stream=True
    )
    response.raise_for_status()
    
    # Write in chunks
    with open(filepath, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:  # Filter out keep-alive chunks
                f.write(chunk)
    
    return filepath

# Usage
for item in mgl.extract("https://pixeldrain.com/l/abc123"):
    filepath = download_streaming(item)
    print(f"Downloaded: {filepath}")
```

## Using DownloadItem.headers

Some platforms require specific HTTP headers for downloads. Always include `item.headers`:

```python
import megaloader as mgl
import requests

for item in mgl.extract("https://bunkr.si/a/abc123"):
    # item.headers might contain Referer or other required headers
    response = requests.get(
        item.download_url,
        headers=item.headers  # IMPORTANT!
    )
    
    # Save file...
```

::: warning Required headers
Some platforms (like Bunkr) require specific headers like `Referer` to prevent hotlinking. Always use `item.headers` in your download requests.
:::

## Organizing by collection

Use `collection_name` to organize downloads into subdirectories:

```python
import megaloader as mgl
import requests
from pathlib import Path

def download_with_collections(item, base_dir: str = "./downloads"):
    """Download and organize by collection."""
    base_path = Path(base_dir)
    
    # Create collection subfolder if needed
    if item.collection_name:
        output_path = base_path / item.collection_name
    else:
        output_path = base_path / "uncategorized"
    
    output_path.mkdir(parents=True, exist_ok=True)
    filepath = output_path / item.filename
    
    # Download
    response = requests.get(item.download_url, headers=item.headers, stream=True)
    response.raise_for_status()
    
    with open(filepath, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    
    return filepath

# Usage
for item in mgl.extract("https://bunkr.si/a/abc123"):
    filepath = download_with_collections(item)
    print(f"Downloaded: {filepath}")
```

This creates a structure like:
```
downloads/
├── Album 1/
│   ├── file1.jpg
│   └── file2.png
├── Album 2/
│   └── file3.mp4
└── uncategorized/
    └── file4.pdf
```

## Progress bars with tqdm

Add progress tracking for better user experience:

```python
import megaloader as mgl
import requests
from pathlib import Path
from tqdm import tqdm

def download_with_progress(item, output_dir: str = "./downloads"):
    """Download with progress bar."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    filepath = output_path / item.filename
    
    # Start download
    response = requests.get(
        item.download_url,
        headers=item.headers,
        stream=True
    )
    response.raise_for_status()
    
    # Get total size from headers
    total_size = int(response.headers.get('content-length', 0))
    
    # Download with progress bar
    with open(filepath, 'wb') as f:
        with tqdm(
            total=total_size,
            unit='B',
            unit_scale=True,
            desc=item.filename
        ) as pbar:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                pbar.update(len(chunk))
    
    return filepath

# Usage
for item in mgl.extract("https://pixeldrain.com/l/abc123"):
    download_with_progress(item)
```

### Multiple files progress

Track progress across multiple files:

```python
import megaloader as mgl
import requests
from pathlib import Path
from tqdm import tqdm

def download_all_with_progress(url: str, output_dir: str = "./downloads"):
    """Download all items with overall progress."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Collect all items first to show total
    items = list(mgl.extract(url))
    
    # Download with progress
    for item in tqdm(items, desc="Downloading", unit="file"):
        filepath = output_path / item.filename
        
        response = requests.get(
            item.download_url,
            headers=item.headers,
            stream=True
        )
        response.raise_for_status()
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

# Usage
download_all_with_progress("https://pixeldrain.com/l/abc123")
```

## Retry logic

Handle transient network failures with automatic retries:

```python
import megaloader as mgl
import requests
from pathlib import Path
import time

def download_with_retry(
    item,
    output_dir: str = "./downloads",
    max_retries: int = 3,
    delay: float = 1.0
):
    """Download with automatic retry on failure."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    filepath = output_path / item.filename
    
    for attempt in range(max_retries):
        try:
            response = requests.get(
                item.download_url,
                headers=item.headers,
                stream=True,
                timeout=30
            )
            response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return filepath  # Success
            
        except (requests.RequestException, IOError) as e:
            if attempt < max_retries - 1:
                print(f"Attempt {attempt + 1} failed: {e}")
                print(f"Retrying in {delay} seconds...")
                time.sleep(delay)
                delay *= 2  # Exponential backoff
            else:
                print(f"Failed after {max_retries} attempts: {item.filename}")
                raise

# Usage
for item in mgl.extract("https://pixeldrain.com/l/abc123"):
    try:
        download_with_retry(item)
    except Exception as e:
        print(f"Skipping {item.filename}: {e}")
```

## Resume downloads

Resume interrupted downloads using HTTP range requests:

```python
import megaloader as mgl
import requests
from pathlib import Path

def download_resumable(item, output_dir: str = "./downloads"):
    """Download with resume support."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    filepath = output_path / item.filename
    
    # Check if partial file exists
    if filepath.exists():
        existing_size = filepath.stat().st_size
        headers = item.headers.copy()
        headers['Range'] = f'bytes={existing_size}-'
        mode = 'ab'  # Append mode
        print(f"Resuming from byte {existing_size}")
    else:
        headers = item.headers
        mode = 'wb'  # Write mode
        existing_size = 0
    
    # Download
    response = requests.get(
        item.download_url,
        headers=headers,
        stream=True
    )
    
    # Check if server supports resume
    if response.status_code == 206:  # Partial Content
        print("Server supports resume")
    elif response.status_code == 200:
        # Server doesn't support resume, start over
        mode = 'wb'
        existing_size = 0
    else:
        response.raise_for_status()
    
    # Write to file
    with open(filepath, mode) as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    
    return filepath

# Usage
for item in mgl.extract("https://pixeldrain.com/l/abc123"):
    download_resumable(item)
```

## Concurrent downloads

Download multiple files simultaneously using thread pools:

```python
import megaloader as mgl
import requests
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

def download_one(item, output_dir: Path):
    """Download a single item (thread-safe)."""
    filepath = output_dir / item.filename
    
    response = requests.get(
        item.download_url,
        headers=item.headers,
        stream=True
    )
    response.raise_for_status()
    
    with open(filepath, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    
    return filepath

def download_concurrent(
    url: str,
    output_dir: str = "./downloads",
    max_workers: int = 5
):
    """Download files concurrently."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Collect all items
    items = list(mgl.extract(url))
    print(f"Found {len(items)} items")
    
    # Download concurrently
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all downloads
        futures = {
            executor.submit(download_one, item, output_path): item
            for item in items
        }
        
        # Process as they complete
        for future in as_completed(futures):
            item = futures[future]
            try:
                filepath = future.result()
                print(f"✓ {filepath.name}")
            except Exception as e:
                print(f"✗ {item.filename}: {e}")

# Usage
download_concurrent(
    "https://pixeldrain.com/l/abc123",
    max_workers=3  # Download 3 files at a time
)
```

::: danger Rate limiting
Be respectful of platform resources. Don't use too many concurrent workers (3-5 is usually reasonable). Some platforms may rate-limit or block excessive concurrent requests.
:::

## Complete download manager

Putting it all together, a production-ready download manager could look like this:

```python
import megaloader as mgl
import requests
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import time

class DownloadManager:
    """Production-ready download manager."""
    
    def __init__(
        self,
        output_dir: str = "./downloads",
        max_workers: int = 3,
        max_retries: int = 3,
        organize_by_collection: bool = True
    ):
        self.output_dir = Path(output_dir)
        self.max_workers = max_workers
        self.max_retries = max_retries
        self.organize_by_collection = organize_by_collection
    
    def _get_output_path(self, item) -> Path:
        """Determine output path for item."""
        if self.organize_by_collection and item.collection_name:
            return self.output_dir / item.collection_name / item.filename
        return self.output_dir / item.filename
    
    def _download_one(self, item) -> tuple[bool, str]:
        """Download a single item with retry logic."""
        filepath = self._get_output_path(item)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        for attempt in range(self.max_retries):
            try:
                response = requests.get(
                    item.download_url,
                    headers=item.headers,
                    stream=True,
                    timeout=30
                )
                response.raise_for_status()
                
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                return True, str(filepath)
                
            except Exception as e:
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    return False, f"Failed: {e}"
        
        return False, "Unknown error"
    
    def download(self, url: str, **extract_options):
        """Download all items from URL."""
        print(f"Extracting metadata from {url}...")
        items = list(mgl.extract(url, **extract_options))
        print(f"Found {len(items)} items\n")
        
        if not items:
            print("No items to download")
            return
        
        # Download with progress
        success_count = 0
        failed_items = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self._download_one, item): item
                for item in items
            }
            
            with tqdm(total=len(items), desc="Downloading", unit="file") as pbar:
                for future in as_completed(futures):
                    item = futures[future]
                    success, result = future.result()
                    
                    if success:
                        success_count += 1
                    else:
                        failed_items.append((item.filename, result))
                    
                    pbar.update(1)
        
        # Summary
        print(f"\n✓ Successfully downloaded: {success_count}/{len(items)}")
        if failed_items:
            print(f"✗ Failed: {len(failed_items)}")
            for filename, error in failed_items:
                print(f"  - {filename}: {error}")

# Usage
manager = DownloadManager(
    output_dir="./downloads",
    max_workers=3,
    organize_by_collection=True
)

# Simple download
manager.download("https://pixeldrain.com/l/abc123")

# With password
manager.download("https://gofile.io/d/xyz789", password="secret")

# Flat structure (no collection folders)
manager_flat = DownloadManager(organize_by_collection=False)
manager_flat.download("https://bunkr.si/a/abc123")
```

## Handling filename conflicts

Prevent overwriting files with duplicate names:

```python
import megaloader as mgl
import requests
from pathlib import Path

def get_unique_filepath(filepath: Path) -> Path:
    """Generate unique filepath if file exists."""
    if not filepath.exists():
        return filepath
    
    stem = filepath.stem
    suffix = filepath.suffix
    parent = filepath.parent
    counter = 1
    
    while True:
        new_path = parent / f"{stem}_{counter}{suffix}"
        if not new_path.exists():
            return new_path
        counter += 1

def download_safe(item, output_dir: str = "./downloads"):
    """Download with automatic filename deduplication."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    filepath = output_path / item.filename
    filepath = get_unique_filepath(filepath)
    
    response = requests.get(item.download_url, headers=item.headers, stream=True)
    response.raise_for_status()
    
    with open(filepath, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    
    return filepath

# Usage
for item in mgl.extract("https://pixeldrain.com/l/abc123"):
    filepath = download_safe(item)
    print(f"Downloaded: {filepath}")
```
