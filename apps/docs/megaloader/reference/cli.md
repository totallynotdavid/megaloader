# CLI reference

Complete reference for all CLI commands and options.

## Command structure

```bash
megaloader [OPTIONS] COMMAND [ARGS]...
```

## Global options

- `--version` - Show version and exit
- `--help` - Show help message and exit

## Commands

### extract

Extract metadata without downloading files.

**Syntax:**

```bash
megaloader extract [OPTIONS] URL
```

**Arguments:**

- `URL` (required) - URL to extract from

**Options:**

- `--json` - Output structured JSON instead of human-readable text
- `-v, --verbose` - Enable debug logging
- `--help` - Show help for extract command

**Exit codes:** 0 (success), 1 (error)

::: details Example output (default)

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

::: details Example output (JSON)

```json
{
  "source": "https://pixeldrain.com/l/DDGtvvTU",
  "count": 6,
  "items": [
    {
      "download_url": "https://pixeldrain.com/api/file/WnQte6cf",
      "filename": "sample-image-01.jpg",
      "collection_name": null,
      "source_id": "WnQte6cf",
      "headers": {},
      "size_bytes": 207558
    },
    {
      "download_url": "https://pixeldrain.com/api/file/qonYV6HZ",
      "filename": "sample-image-02.jpg",
      "collection_name": null,
      "source_id": "qonYV6HZ",
      "headers": {},
      "size_bytes": 405661
    },
    {
      "download_url": "https://pixeldrain.com/api/file/unxLALp7",
      "filename": "sample-image-03.jpg",
      "collection_name": null,
      "source_id": "unxLALp7",
      "headers": {},
      "size_bytes": 286359
    },
    {
      "download_url": "https://pixeldrain.com/api/file/REed9DHV",
      "filename": "sample-image-04.jpg",
      "collection_name": null,
      "source_id": "REed9DHV",
      "headers": {},
      "size_bytes": 412156
    },
    {
      "download_url": "https://pixeldrain.com/api/file/NDhYfoXz",
      "filename": "sample-image-05.jpg",
      "collection_name": null,
      "source_id": "NDhYfoXz",
      "headers": {},
      "size_bytes": 202748
    },
    {
      "download_url": "https://pixeldrain.com/api/file/kaGvShmr",
      "filename": "sample-image-06.jpg",
      "collection_name": null,
      "source_id": "kaGvShmr",
      "headers": {},
      "size_bytes": 89101
    }
  ]
}
```

:::

### download

Download files to a local directory.

**Syntax:**

```bash
megaloader download [OPTIONS] URL [OUTPUT_DIR]
```

**Arguments:**

- `URL` (required) - URL to download from
- `OUTPUT_DIR` (optional) - Output directory (default: `./downloads`)

**Options:**

- `-v, --verbose` - Enable debug logging
- `--flat` - Save files directly to OUTPUT_DIR without collection subfolders
- `--filter PATTERN` - Filter files by glob pattern (e.g., `*.jpg`, `*.mp4`)
- `--password PASSWORD` - Password for protected content
- `--help` - Show help for download command

**Exit codes:** 0 (success), 1 (error)

::: details Example output

```
✓ Using plugin: PixelDrain
Discovering files... ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Found 6 files.

sample-image-01.jpg ━━━━━━━━━━━━━━━━━━━━━ 100% • 0.20 MB • 5.2 MB/s
sample-image-02.jpg ━━━━━━━━━━━━━━━━━━━━━ 100% • 0.39 MB • 6.1 MB/s
sample-image-03.jpg ━━━━━━━━━━━━━━━━━━━━━ 100% • 0.27 MB • 6.3 MB/s
sample-image-04.jpg ━━━━━━━━━━━━━━━━━━━━━ 100% • 0.39 MB • 6.1 MB/s
sample-image-05.jpg ━━━━━━━━━━━━━━━━━━━━━ 100% • 0.19 MB • 5.8 MB/s
sample-image-06.jpg ━━━━━━━━━━━━━━━━━━━━━ 100% • 0.08 MB • 4.9 MB/s

✓ Success! Downloaded 6 files.
```

:::

### plugins

List supported platforms and domains.

**Syntax:**

```bash
megaloader plugins [OPTIONS]
```

**Options:**

- `--help` - Show help for plugins command

**Exit codes:** 0 (always successful)

::: details Output

```
Supported Platforms:

  • bunkr.is             (Bunkr)
  • bunkr.la             (Bunkr)
  • bunkr.ru             (Bunkr)
  • bunkr.si             (Bunkr)
  • bunkr.su             (Bunkr)
  • cyberdrop.cr         (Cyberdrop)
  • cyberdrop.me         (Cyberdrop)
  • cyberdrop.to         (Cyberdrop)
  • fanbox.cc            (Fanbox)
  • fapello.com          (Fapello)
  • gofile.io            (Gofile)
  • pixeldrain.com       (PixelDrain)
  • pixiv.net            (Pixiv)
  • rule34.xxx           (Rule34)
  • thothub.ch           (ThothubTO)
  • thothub.to           (ThothubTO)
  • thothub.vip          (ThothubVIP)
  • thotslife.com        (Thotslife)
```

:::

## Environment variables

**Authentication:**

- `FANBOX_SESSION_ID` - Session cookie for Fanbox
- `PIXIV_SESSION_ID` - Session cookie for Pixiv
- `RULE34_API_KEY` - API key for Rule34
- `RULE34_USER_ID` - User ID for Rule34
- `GOFILE_PASSWORD` - Default password for GoFile

Command-line options take precedence over environment variables.

**Example:**

```bash
export FANBOX_SESSION_ID="your_cookie"
megaloader download "https://creator.fanbox.cc" ./output
```

## Exit codes

- `0` - Success
- `1` - Error (extraction failed, unsupported domain, network error)

Shell scripting:

```bash
if megaloader extract "$URL"; then
    echo "Success"
else
    echo "Failed"
    exit 1
fi
```
