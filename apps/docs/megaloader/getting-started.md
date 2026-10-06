# Getting started

Megaloader turns a link to an album, gallery, or file on a hosting site into a
list of direct download URLs, filenames, and the headers each download needs. It
ships as a command-line tool and as a Python library.

Both need Python 3.10 or newer.

## Install the command-line tool

```bash
pip install megaloader-cli
```

This installs the `megaloader` command and the `megaloader` library it uses.

List what a link holds without downloading anything:

```console
$ megaloader extract https://bunkr.si/a/xYKtNmBx
✓ Using plugin: Bunkr
Extracting metadata... ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Found 6 files:

  01. sample-image-06.jpg
  02. sample-image-04.jpg
  03. sample-image-05.jpg
  04. sample-image-03.jpg
  05. sample-image-01.jpg
  06. sample-image-02.jpg
```

Download the files with `megaloader download URL [OUTPUT_DIR]`. The
[command line](cli) page lists the options.

## Install the library

```bash
pip install megaloader
```

With uv:

```bash
uv add megaloader
```

The library depends on `requests`, `beautifulsoup4`, and `lxml`.

`extract()` yields one `DownloadItem` per file:

```python
import megaloader as mgl

for item in mgl.extract("https://bunkr.si/a/xYKtNmBx"):
    print(item.filename, item.download_url)
```

```text
sample-image-06.jpg https://c1mp-b.cdn.cr/3e48b142-bc3b-4b8d-bbc9-db9f891687d3.jpg?n=sample-image-06.jpg
sample-image-04.jpg https://c1mp-b.cdn.cr/8c385ba6-9650-4bbe-a4a2-45557ad137e1.jpg?n=sample-image-04.jpg
...
```

Megaloader only discovers files. Your code or the CLI downloads them. See
[Downloading files](downloading).

## Try it in the browser

The demo below calls the hosted
[API server](https://github.com/totallynotdavid/megaloader/tree/main/apps/api).

<ApiDemo />

## Next

- [Library](library): the `extract()` function and `DownloadItem`.
- [Platforms](platforms): supported sites and URL shapes.
- [Plugin options](plugin-options): passwords, tokens, and session cookies.
