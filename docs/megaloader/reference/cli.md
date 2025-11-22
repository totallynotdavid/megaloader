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

**Example output (default):**

```
✓ Using plugin: PixelDrain
Extracting metadata... ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Found 6 files:

  01. sample-image-01.jpg
      Size: 0.20 MB
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
      "size_bytes": 207558
    }
  ]
}
```

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

**Example output:**

```
✓ Using plugin: PixelDrain
Discovering files... ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Found 6 files.

sample-image-01.jpg ━━━━━━━━━━━━━━━━━━━━━ 100% • 0.20 MB • 5.2 MB/s
sample-image-02.jpg ━━━━━━━━━━━━━━━━━━━━━ 100% • 0.39 MB • 6.1 MB/s

✓ Success! Downloaded 6 files.
```

### plugins

List supported platforms and domains.

**Syntax:**

```bash
megaloader plugins [OPTIONS]
```

**Options:**

- `--help` - Show help for plugins command

**Exit codes:** 0 (always successful)

**Example output:**

```
Supported Platforms:

  • bunkr.is             (Bunkr)
  • bunkr.la             (Bunkr)
  • cyberdrop.cr         (Cyberdrop)
  • fanbox.cc            (Fanbox)
  • gofile.io            (Gofile)
  • pixeldrain.com       (PixelDrain)
  • pixiv.net            (Pixiv)
  • rule34.xxx           (Rule34)
```

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
