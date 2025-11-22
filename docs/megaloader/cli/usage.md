---
title: CLI usage
description:
  Command-line interface for extracting metadata and downloading files
outline: [2, 3]
prev:
  text: "API reference"
  link: "/core/api"
next:
  text: "CLI examples"
  link: "/cli/examples"
---

# CLI usage

The Megaloader CLI provides terminal-based access to extraction and downloading
functionality. It's a separate package from the core library.

## Installation

You can install via pip:

```bash
pip install megaloader-cli
```

You can also download the binary from the
[release page](https://github.com/totallynotdavid/megaloader/releases) of the
repository.

Verify it's installed:

```bash
megaloader --version
```

## Three main commands

The CLI has three commands: `extract` for dry runs, `download` for actual
downloads, and `plugins` to list supported platforms.

### extract

Preview what files are available without downloading:

```bash
megaloader extract "https://pixeldrain.com/l/abc123"
```

Output shows files with their metadata:

```
✓ Using plugin: PixelDrainPlugin
Extracting metadata... ━━━━━━━━━━━━━━━━━━━━━ 100%

Found 3 files:

  01. image001.jpg
      Collection: My Photos
      Size: 2.45 MB

  02. image002.jpg
      Collection: My Photos
      Size: 3.12 MB

  03. document.pdf
      Collection: My Photos
      Size: 0.89 MB
```

Get structured JSON output instead:

```bash
megaloader extract "https://pixeldrain.com/l/abc123" --json
```

This returns:

```json
{
  "source": "https://pixeldrain.com/l/abc123",
  "count": 3,
  "items": [
    {
      "download_url": "https://pixeldrain.com/api/file/xyz789",
      "filename": "image001.jpg",
      "collection_name": "My Photos",
      "size_bytes": 2568192
    }
  ]
}
```

Enable debug logging to see what's happening:

```bash
megaloader extract "https://pixeldrain.com/l/abc123" --verbose
```

### download

Download files to a directory:

```bash
megaloader download "https://pixeldrain.com/l/abc123" ./my-downloads
```

The output directory is optional and defaults to `./downloads`:

```bash
megaloader download "https://pixeldrain.com/l/abc123"
```

You'll see progress bars for each file:

```
✓ Using plugin: PixelDrainPlugin
Discovering files... ━━━━━━━━━━━━━━━━━━━━━ 100%
✓ Found 3 files.

image001.jpg    ━━━━━━━━━━━━━━━━━━━━━ 100% • 2.45 MB • 5.2 MB/s • 0:00:00
image002.jpg    ━━━━━━━━━━━━━━━━━━━━━ 100% • 3.12 MB • 6.1 MB/s • 0:00:00
document.pdf    ━━━━━━━━━━━━━━━━━━━━━ 100% • 0.89 MB • 4.8 MB/s • 0:00:00

✓ Success! Downloaded 3 files.
Location: /path/to/my-downloads
```

By default, files are organized into subfolders by collection. Disable this with
`--flat`:

```bash
megaloader download "https://pixeldrain.com/l/abc123" ./downloads --flat
```

Filter files by pattern:

```bash
# Only JPG files
megaloader download "https://pixeldrain.com/l/abc123" ./images --filter "*.jpg"

# Only videos
megaloader download "https://pixeldrain.com/l/abc123" ./videos --filter "*.mp4"
```

Provide a password for protected content:

```bash
megaloader download "https://gofile.io/d/abc123" ./downloads --password "secret"
```

### plugins

List all supported platforms:

```bash
megaloader plugins
```

Output shows domains and their plugin classes:

```
Supported Platforms:

  • bunkr.si              (BunkrPlugin)
  • bunkr.su              (BunkrPlugin)
  • cyberdrop.me          (CyberdropPlugin)
  • fanbox.cc             (FanboxPlugin)
  • gofile.io             (GofilePlugin)
  • pixeldrain.com        (PixelDrainPlugin)
  • pixiv.net             (PixivPlugin)
  • rule34.xxx            (Rule34Plugin)
  ...
```

## Global options

These work with all commands:

```bash
megaloader --version      # Show version
megaloader --help         # Show help
megaloader extract --help # Help for specific command
```

## Environment variables

The CLI respects environment variables for credentials:

```bash
export FANBOX_SESSION_ID="your_cookie"
export PIXIV_SESSION_ID="your_cookie"
export RULE34_API_KEY="your_key"
export RULE34_USER_ID="your_id"

megaloader download "https://creator.fanbox.cc" ./output
```

Command-line options take precedence over environment variables. See
[plugin options](/plugins/options) for details on authentication.

## Exit codes

The CLI uses standard exit codes:

- `0` = Success
- `1` = Error (extraction failed, unsupported domain, etc.)

This makes shell scripting easy:

```bash
if megaloader extract "$URL"; then
    echo "Extraction successful"
    megaloader download "$URL" ./output
else
    echo "Extraction failed"
fi
```

## When to use CLI vs library

Use the CLI when you need quick one-off downloads, shell scripting, or just want
to explore what's available on a URL without writing code.

Use the library when you need custom download logic, want to process items
programmatically, or are building an application (website, bots for Discord or
WhatsApp) that integrates extraction.

The CLI is essentially a convenience wrapper around the core library with
progress bars and organized output.
