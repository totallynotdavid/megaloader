# Getting started

Megaloader extracts downloadable file metadata from file hosting platforms. It doesn't download files—instead, it gives you URLs, filenames, and metadata so you can implement downloads however you want.

This guide will get you from installation to your first extraction in just a few minutes.

## Requirements

- Python 3.10 or higher
- pip or uv package manager (uv recommended)

## Installation

Install the core library for programmatic usage:

::: code-group

```bash [uv (recommended)]
uv pip install megaloader
```

```bash [pip]
pip install megaloader
```

:::

This installs the `megaloader` package, which provides the `extract()` function and related APIs for metadata extraction.

<!-- prettier-ignore -->
::: tip Why uv?
uv is significantly faster than pip and provides better dependency resolution.
[Learn more about uv](https://docs.astral.sh/uv/)
:::

**Installing the CLI tool**

The command-line interface is distributed as a separate package. Install it if you want to use Megaloader from the terminal:

::: code-group

```bash [uv (recommended)]
uv pip install megaloader-cli
```

```bash [pip]
pip install megaloader-cli
```

:::

<!-- prettier-ignore -->
::: info Automatic dependencies
The CLI package automatically installs the core library as a dependency. You don't need to install both.
:::

**Verify installation**

Check that the core library is installed:

```python
import megaloader as mgl
print(mgl.__version__)
```

Output:

```
0.2.0
```

If you installed the CLI, verify it works:

```bash
uv run megaloader --version
```

Output:

```
megaloader, version 0.1.0
```

List supported platforms:

```bash
uv run megaloader plugins
```

Output:

```
Supported Platforms:

  • bunkr.is             (Bunkr)
  • bunkr.la             (Bunkr)
  • cyberdrop.cr         (Cyberdrop)
  • cyberdrop.me         (Cyberdrop)
  • fanbox.cc            (Fanbox)
  • fapello.com          (Fapello)
  • gofile.io            (Gofile)
  • pixeldrain.com       (PixelDrain)
  • pixiv.net            (Pixiv)
  • rule34.xxx           (Rule34)
  • thothub.to           (ThothubTO)
  • thothub.vip          (ThothubVIP)
  • thotslife.com        (Thotslife)
```

**Install from source**

For development or to use the latest unreleased features:

```bash
# Clone the repository
git clone https://github.com/totallynotdavid/megaloader.git
cd megaloader

# Install core library
uv pip install -e packages/core

# Optionally install CLI
uv pip install -e packages/cli
```

For contributors working on Megaloader itself, install all workspace dependencies including dev tools:

```bash
uv sync --all-groups
```

This installs additional tools like pytest, ruff, and mypy for testing and code quality.

## Your first extraction

The simplest way to use Megaloader is the `extract()` function:

```python
import megaloader as mgl

for item in mgl.extract("https://pixeldrain.com/l/DDGtvvTU"):
    print(item.filename)
```

That's it. The function returns a generator that yields `DownloadItem` objects containing metadata for each file.

Output:

```
sample-image-01.jpg
sample-image-02.jpg
sample-image-03.jpg
sample-image-04.jpg
sample-image-05.jpg
sample-image-06.jpg
```

Network requests happen lazily during iteration, not when you call `extract()`. This means you can start processing results immediately without waiting for all files to be discovered.

## What you get back

Each item contains everything you need to download the file:

```python
for item in mgl.extract("https://pixeldrain.com/l/DDGtvvTU"):
    print(f"{item.filename} - {item.size_bytes} bytes")
```

Output:

```
sample-image-01.jpg - 207558 bytes
sample-image-02.jpg - 393216 bytes
sample-image-03.jpg - 276480 bytes
sample-image-04.jpg - 393216 bytes
sample-image-05.jpg - 196608 bytes
sample-image-06.jpg - 81920 bytes
```

The `DownloadItem` object includes:

- `download_url` — Direct download URL
- `filename` — Original filename
- `size_bytes` — File size (if available)
- `collection_name` — Album/gallery name
- `headers` — Required HTTP headers

Some fields like `size_bytes` and `collection_name` might be `None` depending on what the platform provides.

## Implementing downloads

Megaloader separates extraction from downloading. It gives you the direct URLs and the exact headers required by the host, and you handle the actual downloading.

```python
import megaloader as mgl
import requests
from pathlib import Path

output = Path("./downloads")
output.mkdir(exist_ok=True)

for item in mgl.extract("https://pixeldrain.com/l/DDGtvvTU"):
    response = requests.get(item.download_url, headers=item.headers)
    
    filepath = output / item.filename
    filepath.write_bytes(response.content)
    print(f"Downloaded: {item.filename}")
```

A few things are happening here:

1. `mgl.extract()` returns one `DownloadItem` at a time. Each item includes a direct download URL and a set of headers the host requires for the request to succeed. Without these headers, many platforms will refuse the download.
2. `requests.get()` uses those headers to retrieve the file.
3. The downloaded data is written to the `./downloads` folder using `Path.write_bytes()`.

**Why keep downloads separate?** Megaloader's job is to provide reliable URLs and the request data that must be used. Everything else is up to you: streaming, retries, concurrency, filtering, or integrating downloads into your own tools.

## Using the CLI

If you installed `megaloader-cli`, you can use it directly from your terminal.

Preview the files in a link without downloading:

```bash
uv run megaloader extract "https://pixeldrain.com/l/DDGtvvTU"
```

Output:

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

Download everything into a folder:

```bash
uv run megaloader download "https://pixeldrain.com/l/DDGtvvTU" ./downloads
```

The CLI handles the downloading and organizes files for you. Use it for quick tasks or whenever you don't need custom logic.

## Platform-specific options

Some platforms support additional parameters that you may need to provide depending on the situation.

**Password-protected links**

GoFile links can be password-protected. If so, pass the password when extracting:

```python
for item in mgl.extract("https://gofile.io/d/abc123", password="secret"):
    print(item.filename)
```

**Authentication for Pixiv and Fanbox**

Pixiv and Fanbox often require authentication to access the full set of files. Without it, Megaloader may return fewer items than you see on the website. You can supply your session cookie through the `session_id` argument:

```python
for item in mgl.extract(
    "https://pixiv.net/user/123",
    session_id="your_cookie"
):
    print(item.filename)
```

<!-- prettier-ignore -->
::: warning A known problem
Using a session ID improves access but does not guarantee identical results to browsing directly
:::

Check the [plugin options](/reference/plugin-options) page to see what each platform supports.

## Error handling

Wrap extraction in try-except to handle problems gracefully:

```python
import megaloader as mgl

try:
    items = list(mgl.extract(url))
except mgl.UnsupportedDomainError as e:
    print(f"Platform not supported: {e.domain}")
except mgl.ExtractionError as e:
    print(f"Extraction failed: {e}")
```

The two main exceptions you'll see are `UnsupportedDomainError` when the platform isn't supported, and `ExtractionError` for network or parsing failures.

## Complete example

Here's everything together with basic error handling:

```python
import megaloader as mgl
import requests
from pathlib import Path

def download_from_url(url: str, output_dir: str = "./downloads"):
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    try:
        items = list(mgl.extract(url))
        print(f"Found {len(items)} files")
        
        for i, item in enumerate(items, 1):
            print(f"[{i}/{len(items)}] {item.filename}...")
            
            # Organize by collection if available
            if item.collection_name:
                file_path = output_path / item.collection_name / item.filename
            else:
                file_path = output_path / item.filename
            
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            response = requests.get(item.download_url, headers=item.headers)
            response.raise_for_status()
            file_path.write_bytes(response.content)
    
    except mgl.UnsupportedDomainError as e:
        print(f"Platform '{e.domain}' isn't supported")
    except mgl.ExtractionError as e:
        print(f"Extraction failed: {e}")

download_from_url("https://pixeldrain.com/l/DDGtvvTU")
```

## Next steps

Now that you've seen the basics, you can:

- Learn about [basic usage](/guide/basic-usage) for deeper understanding
- See [download implementations](/guide/download-implementation) with progress bars and retry logic
- Explore [advanced usage](/guide/advanced-usage) for batch processing and concurrency
- Check [CLI usage](/guide/cli-usage) for terminal-based workflows
- Browse [supported platforms](/reference/plugin-platforms) to see what's available

The library is intentionally minimal. Extraction is the hard part, downloading is just HTTP requests. You have full control over how files get saved.
