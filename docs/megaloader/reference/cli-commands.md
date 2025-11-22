# CLI commands reference

Complete reference for all Megaloader CLI commands, options, and arguments.

## Command structure

```bash
megaloader [OPTIONS] COMMAND [ARGS]...
```

## Global options

**`--version`** Show the version and exit.

**`--help`** Show help message and exit.

## Commands

### extract

Extract metadata from a URL without downloading files (dry run).

**Syntax:**

```bash
megaloader extract [OPTIONS] URL
```

**Arguments:**

- `URL` (required) - The URL to extract metadata from

**Options:**

**`--json`** Output structured JSON instead of human-readable text. Useful for
automation and piping to other tools.

**`-v, --verbose`** Enable debug logging to see detailed extraction process.

**`--help`** Show help for the extract command.

**Exit codes:**

- `0` - Extraction successful
- `1` - Extraction failed (unsupported domain, network error, etc.)

**Example output (default):**

```
✓ Using plugin: PixelDrain
Extracting metadata... ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Found 6 files:

  01. sample-image-01.jpg
      Size: 0.20 MB
  02. sample-image-02.jpg
      Size: 0.39 MB
```

**Example output (JSON):**

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
    }
  ]
}
```

### download

Download files from a URL to a local directory.

**Syntax:**

```bash
megaloader download [OPTIONS] URL [OUTPUT_DIR]
```

**Arguments:**

- `URL` (required) - The URL to download from
- `OUTPUT_DIR` (optional) - Output directory path (default: `./downloads`)

**Options:**

**`-v, --verbose`** Enable debug logging to see detailed download process.

**`--flat`** Save all files directly to OUTPUT_DIR without creating collection
subfolders. By default, files are organized into subfolders by collection name.

**`--filter PATTERN`** Filter files by glob pattern. Only files matching the
pattern will be downloaded.

Examples: `*.jpg`, `*.mp4`, `photo*`, `*2024*`

**`--password PASSWORD`** Password for protected content. Required for
password-protected GoFile links.

**`--help`** Show help for the download command.

**Exit codes:**

- `0` - Download successful
- `1` - Download failed (unsupported domain, network error, etc.)

**Example output:**

```
✓ Using plugin: PixelDrain
Discovering files... ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Found 6 files.

sample-image-01.jpg ━━━━━━━━━━━━━━━━━━━━━ 100% • 0.20 MB • 5.2 MB/s • 0:00:00
sample-image-02.jpg ━━━━━━━━━━━━━━━━━━━━━ 100% • 0.39 MB • 6.1 MB/s • 0:00:00

✓ Success! Downloaded 6 files.
Location: /path/to/downloads
```

### plugins

List all supported platforms and domains.

**Syntax:**

```bash
megaloader plugins [OPTIONS]
```

**Options:**

**`--help`** Show help for the plugins command.

**Exit codes:**

- `0` - Always successful

**Example output:**

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

## Environment variables

The CLI respects environment variables for authentication and configuration.

**Authentication:**

- `FANBOX_SESSION_ID` - Session cookie for Fanbox
- `PIXIV_SESSION_ID` - Session cookie for Pixiv
- `RULE34_API_KEY` - API key for Rule34
- `RULE34_USER_ID` - User ID for Rule34
- `GOFILE_PASSWORD` - Default password for GoFile (overridden by `--password`)

Command-line options take precedence over environment variables.

**Example:**

```bash
export FANBOX_SESSION_ID="your_cookie"
megaloader download "https://creator.fanbox.cc" ./output
```

## Exit codes

All commands use standard exit codes:

- `0` - Success
- `1` - Error (extraction failed, unsupported domain, network error, etc.)

This enables reliable shell scripting:

```bash
if megaloader extract "$URL"; then
    echo "Extraction successful"
else
    echo "Extraction failed"
    exit 1
fi
```
