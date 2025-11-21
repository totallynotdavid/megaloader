# Command Reference

Complete reference for all Megaloader CLI commands and their options.

## megaloader extract

Extract metadata from a URL without downloading files (dry run).

### Syntax

```bash
megaloader extract [OPTIONS] URL
```

### Arguments

- **`URL`** (required): The URL to extract metadata from

### Options

- **`--json`**: Output structured JSON instead of human-readable text
- **`-v, --verbose`**: Enable debug logging to see extraction details
- **`--help`**: Show command help and exit

### Output Format

#### Human-Readable (Default)

```bash
$ megaloader extract https://pixeldrain.com/l/abc123
✓ Using plugin: PixelDrainPlugin
Extracting metadata... ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%

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

#### JSON Format

```bash
$ megaloader extract --json https://pixeldrain.com/l/abc123
```

```json
{
  "source": "https://pixeldrain.com/l/abc123",
  "count": 3,
  "items": [
    {
      "download_url": "https://pixeldrain.com/api/file/xyz789",
      "filename": "image001.jpg",
      "collection_name": "My Photos",
      "source_id": "xyz789",
      "headers": {},
      "size_bytes": 2568192
    },
    {
      "download_url": "https://pixeldrain.com/api/file/abc456",
      "filename": "image002.jpg",
      "collection_name": "My Photos",
      "source_id": "abc456",
      "headers": {},
      "size_bytes": 3271680
    },
    {
      "download_url": "https://pixeldrain.com/api/file/def123",
      "filename": "document.pdf",
      "collection_name": "My Photos",
      "source_id": "def123",
      "headers": {},
      "size_bytes": 933888
    }
  ]
}
```

### Use Cases

- Preview what files are available before downloading
- Export metadata to JSON for processing with other tools
- Verify URL is supported and accessible
- Debug extraction issues with `--verbose`

---

## megaloader download

Download files from a URL to a local directory.

### Syntax

```bash
megaloader download [OPTIONS] URL [OUTPUT_DIR]
```

### Arguments

- **`URL`** (required): The URL to download from
- **`OUTPUT_DIR`** (optional): Destination directory (default: `./downloads`)

### Options

- **`-v, --verbose`**: Enable debug logging
- **`--flat`**: Save all files directly to OUTPUT_DIR without collection subfolders
- **`--filter PATTERN`**: Filter files by glob pattern (e.g., `*.jpg`, `*.mp4`)
- **`--password PASSWORD`**: Password for protected content (Gofile)
- **`--help`**: Show command help and exit

### Collection Organization

By default, files are organized into subfolders based on their `collection_name`:

```
downloads/
├── Album 1/
│   ├── photo1.jpg
│   └── photo2.jpg
└── Album 2/
    ├── video1.mp4
    └── video2.mp4
```

Use `--flat` to disable this behavior and save all files directly to the output directory:

```
downloads/
├── photo1.jpg
├── photo2.jpg
├── video1.mp4
└── video2.mp4
```

### Output Format

```bash
$ megaloader download https://pixeldrain.com/l/abc123 ./my-downloads
✓ Using plugin: PixelDrainPlugin
Discovering files... ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%
✓ Found 3 files.

image001.jpg          ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% • 2.45 MB • 5.2 MB/s • 0:00:00
image002.jpg          ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% • 3.12 MB • 6.1 MB/s • 0:00:00
document.pdf          ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% • 0.89 MB • 4.8 MB/s • 0:00:00

✓ Success! Downloaded 3 files.
Location: /path/to/my-downloads
```

### Examples

Download to default directory:

```bash
megaloader download https://pixeldrain.com/l/abc123
```

Download to specific directory:

```bash
megaloader download https://pixeldrain.com/l/abc123 ./my-files
```

Download without collection subfolders:

```bash
megaloader download --flat https://pixeldrain.com/l/abc123 ./downloads
```

Download only images:

```bash
megaloader download --filter "*.jpg" https://pixeldrain.com/l/abc123 ./images
```

Download only videos:

```bash
megaloader download --filter "*.mp4" https://pixeldrain.com/l/abc123 ./videos
```

Download password-protected content:

```bash
megaloader download --password "secret123" https://gofile.io/d/abc123 ./downloads
```

---

## megaloader plugins

List all supported platforms and their domains.

### Syntax

```bash
megaloader plugins
```

### Options

- **`--help`**: Show command help and exit

### Output Format

```bash
$ megaloader plugins

Supported Platforms:

  • bunkr.si              (BunkrPlugin)
  • bunkr.su              (BunkrPlugin)
  • cyberdrop.me          (CyberdropPlugin)
  • fanbox.cc             (FanboxPlugin)
  • fapello.com           (FapelloPlugin)
  • gofile.io             (GofilePlugin)
  • pixeldrain.com        (PixelDrainPlugin)
  • pixiv.net             (PixivPlugin)
  • rule34.xxx            (Rule34Plugin)
  • thothub.to            (ThotHubToPlugin)
  • thothub.vip           (ThotHubVipPlugin)
  • thotslife.com         (ThotsLifePlugin)
```

### Use Cases

- Check if a platform is supported
- Find the plugin name for a domain
- Verify CLI installation includes all plugins

---

## Global Options

These options work with all commands:

- **`--version`**: Show version and exit
- **`--help`**: Show help message and exit

### Examples

Check CLI version:

```bash
megaloader --version
```

Get help for any command:

```bash
megaloader --help
megaloader extract --help
megaloader download --help
```

---

## Exit Codes

The CLI uses standard exit codes:

- **`0`**: Success
- **`1`**: Error (extraction failed, download failed, unsupported domain, etc.)

This makes it easy to use in shell scripts:

```bash
if megaloader extract "$URL"; then
    echo "Extraction successful"
else
    echo "Extraction failed"
fi
```

---

## Environment Variables

The CLI respects the same environment variables as the core library for plugin-specific authentication:

- **`FANBOX_SESSION_ID`**: Fanbox session cookie
- **`PIXIV_SESSION_ID`**: Pixiv session cookie
- **`RULE34_API_KEY`**: Rule34 API key
- **`RULE34_USER_ID`**: Rule34 user ID

Command-line options (like `--password`) take precedence over environment variables.

See [Plugin Options](/plugins/plugin-options) for details on authentication.
