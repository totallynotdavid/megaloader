# Downloading files

Megaloader gives you metadata. You implement downloads. This separation allows
you to integrate with existing async pipelines, job queues, or specific HTTP
clients.

Here's how, from simple to more complex patterns.

## Basic download

The most critical requirement is respecting the `headers` provided in the
`DownloadItem`.

```python
import megaloader as mgl
import requests
from pathlib import Path

output = Path("./downloads")
output.mkdir(exist_ok=True)

for item in mgl.extract("https://pixeldrain.com/l/abc123"):
    response = requests.get(item.download_url, headers=item.headers)
    response.raise_for_status()

    filepath = output / item.filename
    filepath.write_bytes(response.content)
```

This works for small files but loads each entirely into memory. Not ideal for
large files (videos for example).

## Streaming for large files

For large files, stream in chunks:

```python{10}
def download_streaming(item, output_dir="./downloads"):
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    filepath = output_path / item.filename

    response = requests.get(
        item.download_url,
        headers=item.headers,
        stream=True
    )
    response.raise_for_status()

    with open(filepath, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)

    return filepath
```

The `stream=True` parameter prevents loading the entire response into memory. We
write it in 8KB chunks instead.

## Organizing by collection

Use `collection_name` to maintain album structure:

```python
def download_organized(item, base_dir="./downloads"):
    base_path = Path(base_dir)

    if item.collection_name:
        output_path = base_path / item.collection_name
    else:
        output_path = base_path / "uncategorized"

    output_path.mkdir(parents=True, exist_ok=True)
    filepath = output_path / item.filename

    response = requests.get(item.download_url, headers=item.headers, stream=True)
    response.raise_for_status()

    with open(filepath, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    return filepath
```

This creates folders for each collection like this:

```
downloads/
├── Album 1/
│   ├── photo1.jpg
│   └── photo2.jpg
└── Album 2/
    └── video.mp4
```

## Progress tracking

When building a CLI tool, it’s helpful to provide visual feedback during
downloads. The example below shows how to track progress for a single file using
tqdm:

```python
from tqdm import tqdm

def download_with_progress(item, output_dir="./downloads"):
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    filepath = output_path / item.filename

    response = requests.get(
        item.download_url,
        headers=item.headers,
        stream=True
    )
    response.raise_for_status()

    total_size = int(response.headers.get('content-length', 0))

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
```

For multiple files, track overall progress:

```python
items = list(mgl.extract(url))

for item in tqdm(items, desc="Downloading", unit="file"):
    download_with_progress(item)
```

## Retry logic

```python
import time

def download_with_retry(item, output_dir="./downloads", max_retries=3):
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    filepath = output_path / item.filename
    delay = 1.0

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

            return filepath

        except (requests.RequestException, IOError) as e:
            if attempt < max_retries - 1:
                print(f"Attempt {attempt + 1} failed, retrying in {delay}s...")
                time.sleep(delay)
                delay *= 2
            else:
                raise
```

Exponential backoff handles transient network failures.

## Resume support

To support resuming, inspect the local file size and send the `Range` header.

```python{12}
def download_resumable(item, output_dir="./downloads"):
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    filepath = output_path / item.filename

    if filepath.exists():
        existing_size = filepath.stat().st_size

        # Copy headers to avoid mutating the original item
        headers = item.headers.copy()
        headers['Range'] = f'bytes={existing_size}-'
        mode = 'ab'
    else:
        headers = item.headers
        mode = 'wb'

    response = requests.get(
        item.download_url,
        headers=headers,
        stream=True
    )

    if response.status_code == 200:
        mode = 'wb'
    elif response.status_code != 206:
        response.raise_for_status()

    with open(filepath, mode) as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    return filepath
```

Status 206 means resume is supported. Status 200 means start over (server
ignored Range header).

## Handling filename conflicts

Prevent overwriting files with duplicate names:

```python
def get_unique_filepath(filepath):
    if not filepath.exists():
        return filepath

    stem = filepath.stem
    suffix = filepath.suffix
    counter = 1

    while True:
        new_path = filepath.parent / f"{stem}_{counter}{suffix}"
        if not new_path.exists():
            return new_path
        counter += 1

filepath = output_path / item.filename
filepath = get_unique_filepath(filepath)
```

This appends `_1`, `_2`, etc. to duplicate filenames.

## Concurrent downloads

Since downloading is I/O bound, threading significantly improves throughput.

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def download_one(item, output_dir):
    output_path = Path(output_dir)
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

    return filepath

def download_concurrent(url, output_dir="./downloads", max_workers=3):
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    items = list(mgl.extract(url))

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(download_one, item, output_path): item
            for item in items
        }

        for future in as_completed(futures):
            item = futures[future]
            try:
                filepath = future.result()
                print(f"✓ {filepath.name}")
            except Exception as e:
                print(f"✗ {item.filename}: {e}")
```

Use 3-5 workers typically. Excessive parallel requests can trigger rate
limiting.

## Complete manager

Combining all patterns:

```python
class DownloadManager:
    def __init__(
        self,
        output_dir="./downloads",
        max_workers=3,
        max_retries=3,
        organize_by_collection=True
    ):
        self.output_dir = Path(output_dir)
        self.max_workers = max_workers
        self.max_retries = max_retries
        self.organize_by_collection = organize_by_collection

    def _get_output_path(self, item):
        if self.organize_by_collection and item.collection_name:
            return self.output_dir / item.collection_name / item.filename
        return self.output_dir / item.filename

    def _download_one(self, item):
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
                    time.sleep(2 ** attempt)
                else:
                    return False, f"Failed: {e}"

        return False, "Unknown error"

    def download(self, url, **extract_options):
        items = list(mgl.extract(url, **extract_options))

        if not items:
            return

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

        print(f"\nDownloaded: {success_count}/{len(items)}")
        if failed_items:
            print(f"Failed: {len(failed_items)}")

manager = DownloadManager(
    output_dir="./downloads",
    max_workers=3,
    organize_by_collection=True
)

manager.download("https://pixeldrain.com/l/abc123")
```

This handles streaming, retries, concurrency, progress tracking, and collection
organization.

## Final notes

- Always use `item.headers` in requests. Some platforms require specific headers
  to prevent hotlinking.
- Respect rate limits with 3-5 concurrent downloads.
- Handle errors gracefully with retry logic.
- Check available disk space before downloading large collections.
