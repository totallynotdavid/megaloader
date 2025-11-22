# Getting started

Megaloader extracts file metadata from hosting platforms (like PixelDrain,
GoFile or Bunkr). It gives you direct download URLs, filenames, and any required
headers. You choose what to download and how to handle the requests.

## Live demo

You can try the API directly in your browser to see how it works. The
implementation is available in the
[/api/](https://github.com/totallynotdavid/megaloader/tree/main/api) folder of
the repo and is deployed via Vercel.

<ApiDemo />

## Requirements

Megaloader requires Python 3.10 or higher and can be installed with pip, uv, or
any other compatible package manager.

<!-- prettier-ignore -->
::: info
Python 3.10+ is required for modern type annotation syntax (`str | None`). See
[PEP 604](https://peps.python.org/pep-0604/) for details.
:::

## Installation

The project is split into two packages:

- `megaloader`, the core library, used in your Python code.
- `megaloader-cli`, an optional command-line tool, for working from the
  terminal.

### Core library

Install the core library to use `megaloader` in Python:

::: code-group

```bash [pip]
pip install megaloader
```

```bash [uv]
uv add megaloader
```

:::

The core library provides the `extract()` function and all APIs for metadata
extraction. It depends only on requests, BeautifulSoup4 and lxml.

### CLI tool

The command-line interface is optional and distributed separately. This is
recommended if you just want to download files now without writing code.

::: code-group

```bash [pip]
pip install megaloader-cli
```

```bash [uv]
uv add megaloader-cli
```

:::

The CLI includes the core library as a dependency, plus Click for command-line
parsing and Rich for beautiful terminal output.

Verify it works:

::: code-group

```bash [pip]
megaloader --version
```

```bash [uv]
uv run megaloader --version
```

:::

<!-- prettier-ignore-start -->
::: info
If the `megaloader` command is not found, your system may not include Python's
script directory in `PATH`. You can run it through your package manager or
Python directly:

```bash
python -m megaloader extract ...
```
:::
<!-- prettier-ignore-end -->

List supported platforms:

::: code-group

```bash [pip]
megaloader plugins
```

```bash [uv]
uv run megaloader plugins
```

:::

For source installation, see the
[contributing guide](../development/contributing).

## Your first extraction

The simplest way to use Megaloader is the `extract()` function:

```python
import megaloader as mgl

for item in mgl.extract("https://pixeldrain.com/l/DDGtvvTU"):
    print(item.filename)
```

::: details Output

```
sample-image-01.jpg
sample-image-02.jpg
sample-image-03.jpg
sample-image-04.jpg
sample-image-05.jpg
sample-image-06.jpg
```

:::

The function returns a generator that yields `DownloadItem` objects. Network
requests happen lazily during iteration, not when you call the function.

## What you get

Each `DownloadItem` contains everything needed to download the file:

```python
for item in mgl.extract("https://pixeldrain.com/l/DDGtvvTU"):
    print(f"{item.filename} - {item.size_bytes} bytes")
```

::: details Output

```
sample-image-01.jpg - 207558 bytes
sample-image-02.jpg - 393216 bytes
sample-image-03.jpg - 276480 bytes
sample-image-04.jpg - 393216 bytes
sample-image-05.jpg - 196608 bytes
sample-image-06.jpg - 81920 bytes
```

:::

The fields available are `download_url` (required), `filename` (required),
`size_bytes`, `collection_name`, and `headers`. Some fields may be None
depending on what the platform returns.

## Downloading files

Megaloader gives you URLs and headers. You implement downloads:

```python
import requests
from pathlib import Path

output = Path("./downloads")
output.mkdir(exist_ok=True)

for item in mgl.extract("https://pixeldrain.com/l/DDGtvvTU"):
    response = requests.get(item.download_url, headers=item.headers)
    filepath = output / item.filename
    filepath.write_bytes(response.content)
```

Always use `item.headers` in your requests. Some platforms require specific
headers like `Referer` to prevent hotlinking.

## Using the CLI

If you installed `megaloader-cli`, you can use it directly from your terminal.

Preview files without downloading:

::: code-group

```bash [pip]
megaloader extract "https://pixeldrain.com/l/DDGtvvTU"
```

```bash [uv]
uv run megaloader extract "https://pixeldrain.com/l/DDGtvvTU"
```

:::

::: details Output

```
✓ Using plugin: PixelDrain
Extracting metadata... ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Found 6 files:

  01. sample-image-01.jpg
      Size: 0.20 MB
  02. sample-image-02.jpg
      Size: 0.39 MB
  03. sample-image-03.jpg
      Size: 0.27 MB
  04. sample-image-04.jpg
      Size: 0.39 MB
  05. sample-image-05.jpg
      Size: 0.19 MB
  06. sample-image-06.jpg
      Size: 0.08 MB
```

:::

Download to a directory (defaults to `./downloads`):

::: code-group

```bash [pip]
megaloader download "https://pixeldrain.com/l/DDGtvvTU" ./downloads
```

```bash [uv]
uv run megaloader download "https://pixeldrain.com/l/DDGtvvTU" ./downloads
```

:::

List supported platforms:

::: code-group

```bash [pip]
megaloader plugins
```

```bash [uv]
uv run megaloader plugins
```

:::

## Platform-specific options

Some platforms need additional parameters. GoFile supports password-protected
links:

```python
mgl.extract("https://gofile.io/d/abc123", password="secret")
```

Fanbox and Pixiv often require authentication:

```python
mgl.extract("https://creator.fanbox.cc", session_id="your_cookie")
```

Check the [plugin options](/reference/options) reference to see what each
platform supports.

## Error handling

Wrap extraction in try-except to handle problems gracefully:

```python
try:
    items = list(mgl.extract(url))
except mgl.UnsupportedDomainError as e:
    print(f"Platform not supported: {e.domain}")
except mgl.ExtractionError as e:
    print(f"Extraction failed: {e}")
```

The two main exceptions you'll see are `UnsupportedDomainError` when the
platform isn't supported, and `ExtractionError` for network or parsing failures.

## Next steps

Learn core concepts in [using the library](/guide/using-the-library), see
download patterns in [downloading files](/guide/downloading-files), explore
[advanced patterns](/guide/advanced-patterns) for production use, check
[CLI usage](/guide/cli) for terminal workflows, or browse
[supported platforms](/reference/platforms) to see what's available.

The library is intentionally minimal. Extraction is the hard part, downloading
is just HTTP requests. You have full control over how files get saved.
