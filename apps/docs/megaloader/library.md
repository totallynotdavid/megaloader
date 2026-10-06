# Library

`megaloader.extract()` is the whole public API. It picks a plugin from the URL's
domain, runs it, and yields `DownloadItem` objects.

```python
import megaloader as mgl

for item in mgl.extract("https://bunkr.si/a/xYKtNmBx"):
    print(item.filename)
```

`extract()` is a generator. It validates nothing and makes no request until you
iterate it. Wrap the iteration, not the call, in `try`:

```python
try:
    items = list(mgl.extract(url))
except mgl.ExtractionError as e:
    print(e.category, e)
```

See [Errors](errors) for the exceptions.

## Signature

```text
extract(url, *, plugin=None, session=None, timeout=None, **options)
```

| Argument  | Meaning                                                               |
| --------- | --------------------------------------------------------------------- |
| `url`     | The album, gallery, or file URL.                                      |
| `plugin`  | A plugin name such as `"gofile"`, or a `BasePlugin` subclass.         |
| `session` | A `requests.Session` to send requests with.                           |
| `timeout` | Seconds, or a `(connect, read)` tuple. The default is 30 seconds.     |
| `options` | Keyword options for the plugin. See [Plugin options](plugin-options). |

## DownloadItem

Each item is a dataclass:

| Field             | Type             | Meaning                                      |
| ----------------- | ---------------- | -------------------------------------------- |
| `download_url`    | `str`            | Direct URL of the file.                      |
| `filename`        | `str`            | Leaf filename, not empty and not a path.     |
| `collection_name` | `str` or `None`  | Album, gallery, or user the file belongs to. |
| `source_id`       | `str` or `None`  | The platform's identifier for the file.      |
| `headers`         | `dict[str, str]` | Headers the download request must send.      |
| `size_bytes`      | `int` or `None`  | Size, when the platform reports it.          |

`DownloadItem` raises `ValueError` when `download_url` or `filename` is empty,
or when `filename` contains `/`, `\`, or `..`.

Some platforms reject downloads that lack a `Referer`. Send `item.headers` with
every download request. Bunkr, for example, returns:

```python
DownloadItem(
    download_url="https://c1mp-b.cdn.cr/3e48b142-bc3b-4b8d-bbc9-db9f891687d3.jpg?n=sample-image-06.jpg",
    filename="sample-image-06.jpg",
    collection_name=None,
    source_id="55418273",
    headers={"Referer": "https://get.bunkrr.su/"},
    size_bytes=None,
)
```

## Filter items

Items arrive one at a time, so filter while iterating:

```python
images = [
    item
    for item in mgl.extract(url)
    if item.filename.lower().endswith((".jpg", ".png"))
]
```

Stop early once you have enough:

```python
from itertools import islice

first_ten = list(islice(mgl.extract(url), 10))
```

Because the generator is lazy, the plugin stops fetching pages after the tenth
item.

## Group by collection

```python
from collections import defaultdict

by_collection = defaultdict(list)
for item in mgl.extract(url):
    by_collection[item.collection_name or "ungrouped"].append(item)
```

## Choose a plugin

Megaloader matches the URL's domain to a plugin. Name a plugin to skip the
match, for a mirror domain the registry does not know. The plugin still has to
accept the URL's path. Bunkr accepts any host whose path starts with `/a/` or
`/f/`:

```python
mgl.extract("https://bunkr.example/a/abc123", plugin="bunkr")
```

GoFile and Fapello match their own domain in the URL, so a mirror host raises
`ValueError` for them.

Pass a `BasePlugin` subclass to use a plugin of your own without registering it.
See [Writing plugins](writing-plugins).

The registered names are `bunkr`, `cyberdrop`, `fapello`, `gofile`,
`pixeldrain`, `pixiv`, `rule34`, `thothub-to`, `thothub-vip`, and `thotslife`.

List the registered domains in code:

```python
from megaloader.plugins import PLUGIN_REGISTRY

for domain, plugin_class in sorted(PLUGIN_REGISTRY.items()):
    print(domain, plugin_class.__name__)
```

`get_plugin_for_domain(domain)` and `get_plugin_by_name(name)` from the same
module return the plugin class, or `None`.

## Use your own session

Pass a `requests.Session` to add a proxy, a certificate bundle, or cookies:

```python
import requests

session = requests.Session()
session.proxies = {"https": "http://127.0.0.1:8080"}

for item in mgl.extract(url, session=session, timeout=(5, 60)):
    print(item.filename)
```

A session you pass keeps its own headers and gets no default `User-Agent` and no
retries. A session Megaloader creates sends a browser `User-Agent` and retries
`429`, `500`, `502`, `503`, and `504` responses twice with backoff. Plugin
headers and cookies, such as the Pixiv `Referer`, are applied to either kind.

## Logging

Megaloader logs to the `megaloader` logger and installs no handler:

```python
import logging

logging.basicConfig(level=logging.DEBUG)
```

Set `MEGALOADER_LIVE_DEBUG=1` to also log the URL, the status, and the first 500
characters of the body of every HTTP error response at `DEBUG` level. The body
can contain credentials, so leave it unset outside a debugging session.
