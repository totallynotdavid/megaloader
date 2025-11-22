---
title: Quick start
description:
  Learn Megaloader in 5 minutes, from installation to extracting your first
  files
outline: [2, 3]
prev:
  text: "Installation"
  link: "/getting-started/installation"
next:
  text: "Core concepts"
  link: "/core/basics"
---

# Quick start

Megaloader extracts downloadable file metadata from file hosting platforms. It
doesn't download files, instead, it gives you URLs, filenames, and metadata so
you can implement downloads however you want.

## Your first extraction

The simplest way to use Megaloader is the `extract()` function:

```python
import megaloader as mgl

for item in mgl.extract("https://pixeldrain.com/l/abc123"):
    print(f"{item.filename} - {item.download_url}")
```

That's it. The function returns a generator that yields `DownloadItem` objects
containing metadata for each file. Network requests happen lazily during
iteration, not when you call `extract()`.

## What you get back

Each item contains everything you need to download the file:

```python
for item in mgl.extract("https://cyberdrop.me/a/example"):
    print(item.download_url)      # Direct download URL
    print(item.filename)          # Original filename
    print(item.size_bytes)        # File size (if available)
    print(item.collection_name)   # Album/gallery name
    print(item.headers)           # Required HTTP headers
```

Some fields like `size_bytes` and `collection_name` might be `None` depending on
what the platform provides.

## Implementing downloads

Megaloader separates extraction from downloading. It gives you, among other
things, the direct URLs and the exact headers required by the host, and you
handle the actual downloading.

```python{8}
import megaloader as mgl
import requests
from pathlib import Path

output = Path("./downloads")
output.mkdir(exist_ok=True)

for item in mgl.extract("https://pixeldrain.com/u/example"):
    response = requests.get(item.download_url, headers=item.headers)

    filepath = output / item.filename
    filepath.write_bytes(response.content)
    print(f"Downloaded: {item.filename}")
```

A few things are happening in this example:

1. `mgl.extract()` returns one `DownloadItem` at a time. Each item includes a
   direct download URL and a set of headers the host requires for the request to
   succeed. Without these headers, many platforms will refuse the download.
2. `requests.get()` uses those headers to retrieve the file.
3. The downloaded data is written to the `./downloads` folder using
   `Path.write_bytes()`.

**Why keep downloads separate?** Megaloader's job is to provide reliable URLs
and the request data that must be used. Everything else is up to you: streaming,
retries, concurrency, filtering, or integrating downloads into your own tools.

If you prefer something ready to use, the project also includes a CLI you can
read about next.

## Using the CLI

If you installed `megaloader-cli`, you can use it directly from your terminal.

To preview the files in a link without downloading:

```bash
megaloader extract "https://pixeldrain.com/l/abc123"
```

To download everything into a folder named "downloads":

```bash
megaloader download "https://pixeldrain.com/l/abc123" ./downloads
```

To list all supported platforms:

```bash
megaloader plugins
```

The CLI handles the downloading and organizes files for you. Use it for quick
tasks or whenever you don’t need custom logic.

## Platform-specific options

Some platforms support additional parameters that you may need to provide
depending on the situation.

For example, GoFile links can be password-protected. If so, pass the password
when extracting:

```python
for item in mgl.extract("https://gofile.io/d/abc123", password="secret"):
    print(item.filename)
```

Pixiv and Fanbox often require authentication to access the full set of files.
Without it, Megaloader may return fewer items than you see on the website. You
can supply your session cookie through the `session_id` argument:

```python{3}
for item in mgl.extract(
    "https://pixiv.net/user/123",
    session_id="your_cookie"
):
    print(item.filename)
```

Don't worry if you don't know to get your `session_id` yet, the Pixiv section
will have you covered.

<!-- prettier-ignore -->
::: warning A known problem
Using a session ID improves access but does not guarantee identical results to
browsing directly
:::

Check the [plugin options](/plugins/options) page to see what each platform
supports.

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

The two main exceptions you'll see are `UnsupportedDomainError` when the
platform isn't supported, and `ExtractionError` for network or parsing failures.

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

download_from_url("https://pixeldrain.com/l/abc123")
```

## Next steps

Now that you've seen the basics, you can:

- Learn about [core library concepts](/core/basics) for deeper understanding
- See [download implementations](/core/downloads) with progress bars and retry
  logic
- Explore [advanced patterns](/core/advanced) for batch processing and
  concurrency
- Check [CLI usage](/cli/usage) for terminal-based workflows
- Browse [supported platforms](/plugins/platforms) to see what's available

The library is intentionally minimal. Extraction is the hard part, downloading
is just HTTP requests. You have full control over how files get saved.
