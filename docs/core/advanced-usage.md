# Advanced Usage

This guide covers advanced patterns and techniques for working with Megaloader in production environments.

## Direct Plugin Instantiation

While `extract()` automatically selects plugins, you can instantiate them directly for more control:

```python
from megaloader.plugins import PixelDrain

# Direct instantiation
plugin = PixelDrain("https://pixeldrain.com/l/abc123")

# Extract items
for item in plugin.extract():
    print(item.filename)
```

This is useful when you:
- Need to reuse the same plugin instance
- Want to access plugin-specific methods
- Need to customize session configuration

### Custom Session Configuration

Access the underlying requests session for advanced configuration:

```python
from megaloader.plugins import PixelDrain

plugin = PixelDrain("https://pixeldrain.com/l/abc123")

# Access and customize the session
session = plugin.session
session.headers["Custom-Header"] = "value"
session.proxies = {"https": "http://proxy.example.com:8080"}

# Now extract with custom session
for item in plugin.extract():
    print(item.filename)
```

## Batch Processing Multiple URLs

Process multiple URLs efficiently:

```python
import megaloader as mgl

urls = [
    "https://pixeldrain.com/l/abc123",
    "https://gofile.io/d/xyz789",
    "https://bunkr.si/a/def456",
]

def extract_all(urls: list[str]) -> dict[str, list]:
    """Extract items from multiple URLs."""
    results = {}
    
    for url in urls:
        try:
            items = list(mgl.extract(url))
            results[url] = items
            print(f"✓ {url}: {len(items)} items")
        except mgl.UnsupportedDomainError:
            print(f"✗ {url}: Unsupported domain")
            results[url] = []
        except mgl.ExtractionError as e:
            print(f"✗ {url}: {e}")
            results[url] = []
    
    return results

# Process all URLs
all_items = extract_all(urls)

# Summary
total = sum(len(items) for items in all_items.values())
print(f"\nTotal: {total} items from {len(urls)} URLs")
```

## Progress Tracking

Track extraction progress with real-time feedback:

```python
import megaloader as mgl
from rich.progress import Progress, SpinnerColumn, TextColumn

def extract_with_progress(url: str):
    """Extract items with progress indicator."""
    items = []
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
    ) as progress:
        task = progress.add_task("Extracting...", total=None)
        
        for item in mgl.extract(url):
            items.append(item)
            progress.update(
                task,
                description=f"Extracting... ({len(items)} items found)"
            )
    
    return items

# Usage
items = extract_with_progress("https://pixeldrain.com/l/abc123")
print(f"Extraction complete: {len(items)} items")
```

### Progress with Known Total

If you know the total count beforehand (e.g., from a previous extraction):

```python
import megaloader as mgl
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn

def extract_with_bar(url: str, expected_count: int):
    """Extract with progress bar."""
    items = []
    
    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeRemainingColumn(),
    ) as progress:
        task = progress.add_task("Extracting", total=expected_count)
        
        for item in mgl.extract(url):
            items.append(item)
            progress.update(task, advance=1)
    
    return items

# Usage (if you know there are ~50 items)
items = extract_with_bar("https://pixeldrain.com/l/abc123", expected_count=50)
```

## Collection Organization

Organize extracted items by collection for structured processing:

```python
import megaloader as mgl
from pathlib import Path
from collections import defaultdict

def organize_by_collection(url: str) -> dict[str, list]:
    """Group items by collection name."""
    collections = defaultdict(list)
    
    for item in mgl.extract(url):
        collection = item.collection_name or "uncategorized"
        collections[collection].append(item)
    
    return dict(collections)

# Usage
collections = organize_by_collection("https://bunkr.si/a/abc123")

for collection_name, items in collections.items():
    print(f"\n{collection_name}:")
    for item in items:
        print(f"  - {item.filename}")
```

### Creating Collection Directories

Prepare directory structure based on collections:

```python
import megaloader as mgl
from pathlib import Path

def create_collection_structure(url: str, base_dir: str = "./downloads"):
    """Create directory structure for collections."""
    base_path = Path(base_dir)
    collections = set()
    
    for item in mgl.extract(url):
        if item.collection_name:
            collection_path = base_path / item.collection_name
            collection_path.mkdir(parents=True, exist_ok=True)
            collections.add(item.collection_name)
    
    print(f"Created {len(collections)} collection directories")
    return collections

# Usage
collections = create_collection_structure("https://bunkr.si/a/abc123")
```

## Filtering and Conditional Processing

Apply complex filters during extraction:

```python
import megaloader as mgl
from pathlib import Path

def filter_items(url: str, **filters):
    """Extract items matching filter criteria."""
    items = []
    
    for item in mgl.extract(url):
        # Filter by extension
        if "extensions" in filters:
            ext = Path(item.filename).suffix.lower()
            if ext not in filters["extensions"]:
                continue
        
        # Filter by minimum size
        if "min_size" in filters:
            if not item.size_bytes or item.size_bytes < filters["min_size"]:
                continue
        
        # Filter by maximum size
        if "max_size" in filters:
            if item.size_bytes and item.size_bytes > filters["max_size"]:
                continue
        
        # Filter by collection
        if "collections" in filters:
            if item.collection_name not in filters["collections"]:
                continue
        
        # Filter by filename pattern
        if "pattern" in filters:
            import re
            if not re.search(filters["pattern"], item.filename):
                continue
        
        items.append(item)
    
    return items

# Usage examples

# Only images
images = filter_items(
    url,
    extensions=[".jpg", ".png", ".gif", ".webp"]
)

# Files between 1MB and 100MB
medium_files = filter_items(
    url,
    min_size=1_000_000,
    max_size=100_000_000
)

# Specific collections
selected = filter_items(
    url,
    collections=["Album 1", "Album 2"]
)

# Filename pattern
matching = filter_items(
    url,
    pattern=r"IMG_\d{4}"
)
```

## Deduplication

Remove duplicate items based on various criteria:

```python
import megaloader as mgl

def deduplicate_by_url(items: list) -> list:
    """Remove items with duplicate download URLs."""
    seen_urls = set()
    unique_items = []
    
    for item in items:
        if item.download_url not in seen_urls:
            seen_urls.add(item.download_url)
            unique_items.append(item)
    
    return unique_items

def deduplicate_by_filename(items: list) -> list:
    """Remove items with duplicate filenames."""
    seen_names = set()
    unique_items = []
    
    for item in items:
        if item.filename not in seen_names:
            seen_names.add(item.filename)
            unique_items.append(item)
    
    return unique_items

# Usage
items = list(mgl.extract(url))
print(f"Original: {len(items)} items")

unique_items = deduplicate_by_url(items)
print(f"After deduplication: {len(unique_items)} items")
```

## Metadata Export

Export extracted metadata to various formats:

```python
import megaloader as mgl
import json
import csv

def export_to_json(url: str, output_file: str):
    """Export metadata to JSON."""
    items = []
    
    for item in mgl.extract(url):
        items.append({
            "download_url": item.download_url,
            "filename": item.filename,
            "collection_name": item.collection_name,
            "source_id": item.source_id,
            "size_bytes": item.size_bytes,
            "headers": item.headers,
        })
    
    with open(output_file, 'w') as f:
        json.dump(items, f, indent=2)
    
    print(f"Exported {len(items)} items to {output_file}")

def export_to_csv(url: str, output_file: str):
    """Export metadata to CSV."""
    items = list(mgl.extract(url))
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            "filename", "download_url", "collection_name",
            "size_bytes", "source_id"
        ])
        
        for item in items:
            writer.writerow([
                item.filename,
                item.download_url,
                item.collection_name or "",
                item.size_bytes or "",
                item.source_id or "",
            ])
    
    print(f"Exported {len(items)} items to {output_file}")

# Usage
export_to_json("https://pixeldrain.com/l/abc123", "metadata.json")
export_to_csv("https://pixeldrain.com/l/abc123", "metadata.csv")
```

## Retry Logic for Extraction

Handle transient failures with retry logic:

```python
import megaloader as mgl
import time
from typing import Generator

def extract_with_retry(
    url: str,
    max_retries: int = 3,
    delay: float = 1.0,
    **options
) -> Generator:
    """Extract with automatic retry on failure."""
    for attempt in range(max_retries):
        try:
            yield from mgl.extract(url, **options)
            return  # Success
        except mgl.ExtractionError as e:
            if attempt < max_retries - 1:
                print(f"Attempt {attempt + 1} failed: {e}")
                print(f"Retrying in {delay} seconds...")
                time.sleep(delay)
                delay *= 2  # Exponential backoff
            else:
                print(f"All {max_retries} attempts failed")
                raise

# Usage
for item in extract_with_retry("https://pixeldrain.com/l/abc123"):
    print(item.filename)
```

## Parallel Extraction

Extract from multiple URLs concurrently:

```python
import megaloader as mgl
from concurrent.futures import ThreadPoolExecutor, as_completed

def extract_parallel(urls: list[str], max_workers: int = 5) -> dict:
    """Extract from multiple URLs in parallel."""
    results = {}
    
    def extract_one(url: str):
        try:
            items = list(mgl.extract(url))
            return url, items, None
        except Exception as e:
            return url, [], str(e)
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(extract_one, url): url for url in urls}
        
        for future in as_completed(futures):
            url, items, error = future.result()
            if error:
                print(f"✗ {url}: {error}")
                results[url] = []
            else:
                print(f"✓ {url}: {len(items)} items")
                results[url] = items
    
    return results

# Usage
urls = [
    "https://pixeldrain.com/l/abc123",
    "https://gofile.io/d/xyz789",
    "https://bunkr.si/a/def456",
]

results = extract_parallel(urls, max_workers=3)
total = sum(len(items) for items in results.values())
print(f"\nTotal: {total} items from {len(urls)} URLs")
```

## Caching Extraction Results

Cache extraction results to avoid repeated requests:

```python
import megaloader as mgl
import json
import hashlib
from pathlib import Path
from datetime import datetime, timedelta

class ExtractionCache:
    """Simple file-based cache for extraction results."""
    
    def __init__(self, cache_dir: str = "./.cache", ttl_hours: int = 24):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.ttl = timedelta(hours=ttl_hours)
    
    def _get_cache_path(self, url: str) -> Path:
        """Generate cache file path for URL."""
        url_hash = hashlib.md5(url.encode()).hexdigest()
        return self.cache_dir / f"{url_hash}.json"
    
    def get(self, url: str) -> list | None:
        """Get cached items if available and not expired."""
        cache_path = self._get_cache_path(url)
        
        if not cache_path.exists():
            return None
        
        # Check if cache is expired
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        if datetime.now() - mtime > self.ttl:
            return None
        
        # Load cached data
        with open(cache_path) as f:
            data = json.load(f)
        
        # Reconstruct DownloadItem objects
        from megaloader import DownloadItem
        return [DownloadItem(**item) for item in data]
    
    def set(self, url: str, items: list):
        """Cache extraction results."""
        cache_path = self._get_cache_path(url)
        
        # Convert items to dict for JSON serialization
        data = [
            {
                "download_url": item.download_url,
                "filename": item.filename,
                "collection_name": item.collection_name,
                "source_id": item.source_id,
                "headers": item.headers,
                "size_bytes": item.size_bytes,
            }
            for item in items
        ]
        
        with open(cache_path, 'w') as f:
            json.dump(data, f)

def extract_cached(url: str, cache: ExtractionCache) -> list:
    """Extract with caching."""
    # Try cache first
    cached = cache.get(url)
    if cached:
        print(f"Using cached results ({len(cached)} items)")
        return cached
    
    # Extract and cache
    print("Extracting (not cached)...")
    items = list(mgl.extract(url))
    cache.set(url, items)
    
    return items

# Usage
cache = ExtractionCache(ttl_hours=24)
items = extract_cached("https://pixeldrain.com/l/abc123", cache)
```

## Next Steps

- [Download Implementation](/core/download-implementation) - Implement file downloads
- [API Reference](/core/api-reference) - Complete API documentation
- [Creating Plugins](/plugins/creating-plugins) - Build custom platform extractors
