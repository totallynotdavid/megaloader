# CLI Commands

Complete reference for the Megaloader command-line interface.

## Installation

Install the CLI package:

```bash
uv pip install -e packages/cli
```

## Commands

### megaloader

Main command group.

```bash
megaloader [OPTIONS] COMMAND [ARGS]...
```

**Options:**
- `--version`: Show version and exit
- `--help`: Show help message

### download-url

Download content from a URL.

```bash
megaloader download-url [OPTIONS] URL [OUTPUT_DIR]
```

**Arguments:**
- `URL`: The URL to download from (required)
- `OUTPUT_DIR`: Directory to save files (default: `./downloads`)

**Options:**
- `-v, --verbose`: Enable verbose logging
- `--use-proxy`: Use proxy for downloads
- `--no-subdirs`: Don't create album subdirectories

**Examples:**

Basic download:
```bash
megaloader download-url "https://pixeldrain.com/u/file_id"
```

Download to specific directory:
```bash
megaloader download-url "https://cyberdrop.me/a/album" ./my-downloads
```

Enable verbose output:
```bash
megaloader download-url "https://bunkr.si/a/example" --verbose
```

Use proxy:
```bash
megaloader download-url "https://pixeldrain.com/u/file" --use-proxy
```

Disable subdirectories:
```bash
megaloader download-url "https://cyberdrop.me/a/album" --no-subdirs
```

### list-plugins

List all available plugins and supported platforms.

```bash
megaloader list-plugins
```

**Output Example:**

```
Available Plugins:

  • Bunkr: bunkr.si, bunkr.la, bunkr.is, bunkr.ru, bunkr.su
  • Cyberdrop: cyberdrop.me, cyberdrop.to
  • GoFile: gofile.io
  • PixelDrain: pixeldrain.com
  • Pixiv: pixiv.net
  ...
```

## Exit Codes

- `0`: Success
- `1`: Download failed or error occurred

## Environment Variables

Some plugins require environment variables:

```bash
# GoFile password-protected folders
export GOFILE_PASSWORD=your_password

# Pixiv authentication
export PIXIV_REFRESH_TOKEN=your_token

# Fanbox authentication
export FANBOX_SESSION_ID=your_session
```

Or use a `.env` file:

```bash
# .env
GOFILE_PASSWORD=your_password
PIXIV_REFRESH_TOKEN=your_token
FANBOX_SESSION_ID=your_session
```

## Usage Examples

### Basic Workflow

1. List supported platforms:
```bash
megaloader list-plugins
```

2. Download from a supported platform:
```bash
megaloader download-url "https://pixeldrain.com/u/example" ./downloads
```

3. Check verbose output for debugging:
```bash
megaloader download-url "https://bunkr.si/a/example" --verbose
```

### Batch Downloads

Use shell scripting for multiple downloads:

```bash
# urls.txt
https://pixeldrain.com/u/file1
https://cyberdrop.me/a/album1
https://bunkr.si/a/example

# Download all
while read url; do
  megaloader download-url "$url" ./batch-downloads
done < urls.txt
```

### PowerShell (Windows)

```powershell
# Download multiple URLs
$urls = @(
    "https://pixeldrain.com/u/file1",
    "https://cyberdrop.me/a/album1"
)

foreach ($url in $urls) {
    megaloader download-url $url .\downloads
}
```

## Logging

The CLI uses Rich for formatted output:

- ✓ Success messages in green
- ✗ Error messages in red  
- ⚠ Warnings in yellow
- Progress spinners during downloads

## Troubleshooting

### Command not found

If `megaloader` is not found:

```bash
# Use full path to executable
.\.venv\Scripts\megaloader.exe --version

# Or activate virtual environment
.\.venv\Scripts\Activate.ps1  # Windows
source .venv/bin/activate      # Linux/Mac
```

### Import errors

Ensure the core library is installed:

```bash
uv pip install -e packages/megaloader
```

### Network errors

Use `--verbose` to see detailed error messages:

```bash
megaloader download-url "https://example.com/file" --verbose
```

## See Also

- [Getting Started](../getting-started/quickstart.md)
- [Core API Reference](../api/core.md)
- [Plugin System](../guide/plugins.md)
