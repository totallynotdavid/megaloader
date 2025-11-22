# Advanced patterns

Patterns for production environments and complex workflows.

## Batch processing

```python
import megaloader as mgl

urls = [
    "https://pixeldrain.com/l/abc123",
    "https://gofile.io/d/xyz789",
    "https://bunkr.si/a/def456",
]

results = {}

for url in urls:
    try:
        items = list(mgl.extract(url))
        results[url] = items
        print(f"{url}: {len(items)} items")
    except mgl.UnsupportedDomainError:
        results[url] = []
    except mgl.ExtractionError as e:
        print(f"{url}: {e}")
        results[url] = []

total = sum(len(items) for items in results.values())
print(f"\nTotal: {total} items from {len(urls)} URLs")
```

## Parallel extraction

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def extract_one(url):
    try:
        items = list(mgl.extract(url))
        return url, items, None
    except Exception as e:
        return url, [], str(e)

def extract_parallel(urls, max_workers=5):
    results = {}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(extract_one, url): url for url in urls}

        for future in as_completed(futures):
            url, items, error = future.result()

            if error:
                print(f"{url}: {error}")
            else:
                print(f"{url}: {len(items)} items")

            results[url] = items

    return results

urls = [...]
results = extract_parallel(urls, max_workers=3)
```

## Caching extraction results

```python
import json
import hashlib
from pathlib import Path
from datetime import datetime, timedelta

class ExtractionCache:
    def __init__(self, cache_dir="./.cache", ttl_hours=24):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.ttl = timedelta(hours=ttl_hours)

    def _get_cache_path(self, url):
        url_hash = hashlib.md5(url.encode()).hexdigest()
        return self.cache_dir / f"{url_hash}.json"

    def get(self, url):
        cache_path = self._get_cache_path(url)

        if not cache_path.exists():
            return None

        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        if datetime.now() - mtime > self.ttl:
            return None

        with open(cache_path) as f:
            data = json.load(f)

        from megaloader import DownloadItem
        return [DownloadItem(**item) for item in data]

    def set(self, url, items):
        cache_path = self._get_cache_path(url)

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

cache = ExtractionCache(ttl_hours=24)

cached = cache.get(url)
if cached:
    items = cached
else:
    items = list(mgl.extract(url))
    cache.set(url, items)
```

Caches extraction results for 24 hours, avoiding repeated network requests.

## Complex filtering

Apply multiple criteria:

```python
from pathlib import Path
import re

def filter_items(url, **filters):
    for item in mgl.extract(url):
        # Filter by extension
        if "extensions" in filters:
            ext = Path(item.filename).suffix.lower()
            if ext not in filters["extensions"]:
                continue

        # Filter by size range
        if "min_size" in filters and item.size_bytes:
            if item.size_bytes < filters["min_size"]:
                continue

        if "max_size" in filters and item.size_bytes:
            if item.size_bytes > filters["max_size"]:
                continue

        # Filter by collection
        if "collections" in filters:
            if item.collection_name not in filters["collections"]:
                continue

        # Filter by filename pattern
        if "pattern" in filters:
            if not re.search(filters["pattern"], item.filename):
                continue

        yield item

images = list(filter_items(url, extensions=[".jpg", ".png", ".webp"]))

medium_files = list(filter_items(
    url,
    min_size=1_000_000,
    max_size=100_000_000
))

specific_albums = list(filter_items(
    url,
    collections=["Album 1", "Album 2"]
))

matching_names = list(filter_items(
    url,
    pattern=r"IMG_\d{4}"
))
```

## Deduplication

Remove duplicates by URL or filename:

```python
def deduplicate_by_url(items):
    seen_urls = set()
    unique = []

    for item in items:
        if item.download_url not in seen_urls:
            seen_urls.add(item.download_url)
            unique.append(item)

    return unique

def deduplicate_by_filename(items):
    seen_names = set()
    unique = []

    for item in items:
        if item.filename not in seen_names:
            seen_names.add(item.filename)
            unique.append(item)

    return unique

items = list(mgl.extract(url))
unique = deduplicate_by_url(items)
```

## Exporting metadata

Export to JSON or CSV for external processing:

```python
import json

def export_json(url, output_file):
    items = []

    for item in mgl.extract(url):
        items.append({
            "download_url": item.download_url,
            "filename": item.filename,
            "collection_name": item.collection_name,
            "size_bytes": item.size_bytes,
        })

    with open(output_file, 'w') as f:
        json.dump(items, f, indent=2)

    print(f"Exported {len(items)} items")
```

## Retry with exponential backoff

Handle transient failures:

```python
import time

def extract_with_retry(url, max_retries=3, **options):
    delay = 1.0

    for attempt in range(max_retries):
        try:
            yield from mgl.extract(url, **options)
            return
        except mgl.ExtractionError as e:
            if attempt < max_retries - 1:
                print(f"Attempt {attempt + 1} failed, retrying in {delay}s...")
                time.sleep(delay)
                delay *= 2
            else:
                raise
```

## Direct plugin usage

```python
from megaloader.plugins import PixelDrain

plugin = PixelDrain("https://pixeldrain.com/l/abc123")

plugin.session.headers["Custom-Header"] = "value"
plugin.session.proxies = {"https": "http://proxy.example.com:8080"}

for item in plugin.extract():
    print(item.filename)
```

Useful when you need to reuse a plugin instance or customize the session.

## Extraction pipelines

Chain operations together:

```python
def extract_pipeline(url):
    items = mgl.extract(url)

    # Filter by size
    items = (item for item in items if item.size_bytes and item.size_bytes > 1_000_000)

    # Deduplicate
    seen = set()
    def dedupe(items):
        for item in items:
            if item.download_url not in seen:
                seen.add(item.download_url)
                yield item

    items = dedupe(items)

    # Clean filenames
    def clean_names(items):
        for item in items:
            clean_name = re.sub(r'[<>:"/\\|?*]', '_', item.filename)
            item.filename = clean_name
            yield item

    items = clean_names(items)

    return items

for item in extract_pipeline(url):
    download(item)
```

Everything happens lazily during iteration.

## Progress tracking with rich

```python
from rich.progress import Progress, SpinnerColumn, TextColumn

def extract_with_rich_progress(url):
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
                description=f"Extracting... ({len(items)} found)"
            )

    return items
```

Combine these patterns as needed: caching frequently accessed URLs, running
extractions in parallel for batch jobs, or deduplicating results before
processing.
