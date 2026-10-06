# Downloading files

Megaloader finds files and leaves the transfer to you. This page has recipes
built on `requests`. For a ready-made downloader, use
[`megaloader download`](cli).

Every recipe sends `item.headers`. Hosts such as Bunkr and Pixiv reject
downloads that lack the `Referer` the plugin reports.

## One file

Stream the body to disk so large files never sit in memory:

```python
from pathlib import Path

import requests

import megaloader as mgl


def download(item: mgl.DownloadItem, directory: Path) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / item.filename
    partial = target.with_name(target.name + ".part")

    with requests.get(
        item.download_url, headers=item.headers, stream=True, timeout=60
    ) as response:
        response.raise_for_status()
        with partial.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=1024 * 64):
                handle.write(chunk)

    partial.replace(target)
    return target
```

The file appears under its final name only after the transfer finishes, so an
interrupted run leaves a `.part` file and never a truncated image.

## A whole collection

`collection_name` comes from the site, so it can contain characters that are not
safe in a path. Reduce it to one safe path component before you use it:

```python
import re
from pathlib import Path


def safe_name(name: str) -> str:
    return re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name).strip(" .") or "unnamed"


def download_all(url: str, root: Path) -> None:
    for item in mgl.extract(url):
        directory = root
        if item.collection_name:
            directory = root / safe_name(item.collection_name)
        target = directory / item.filename
        if target.exists():
            print("skip", target)
            continue
        print("get ", download(item, directory))
```

Pass `root` as `Path("downloads")`. Files whose item has no collection go
directly into `root`.

## Several files at once

Download in a thread pool and retry a failed file a few times:

```python
import time
from concurrent.futures import ThreadPoolExecutor, as_completed


def download_with_retry(item: mgl.DownloadItem, directory: Path) -> Path:
    for attempt in range(3):
        try:
            return download(item, directory)
        except requests.RequestException:
            if attempt == 2:
                raise
            time.sleep(2**attempt)


def download_parallel(url: str, directory: Path, workers: int = 4) -> None:
    items = list(mgl.extract(url))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(download_with_retry, item, directory): item
            for item in items
        }
        for future in as_completed(futures):
            item = futures[future]
            try:
                print("done", future.result())
            except requests.RequestException as e:
                print("fail", item.filename, e)
```

Hosts can throttle aggressive clients, so start with a few workers.

## Check the size first

Not every plugin reports `size_bytes`. Ask the server with a `HEAD` request when
you need it before you commit to a download:

```python
def remote_size(item: mgl.DownloadItem) -> int | None:
    response = requests.head(
        item.download_url, headers=item.headers, allow_redirects=True, timeout=30
    )
    length = response.headers.get("Content-Length")
    return int(length) if length else None
```

A server can omit `Content-Length`. Treat `None` as "unknown".
