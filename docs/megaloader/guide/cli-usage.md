# CLI usage

The Megaloader CLI provides terminal-based access to extraction and downloading
functionality. It's a thin wrapper around the core library that adds progress
tracking, organized output, and convenient command-line options.

## Installation

Install the CLI as a separate package:

```bash
pip install megaloader-cli
```

Verify it's installed:

```bash
megaloader --version
```

Output:

```
megaloader, version 0.1.0
```

You can also download pre-built binaries from the
[release page](https://github.com/totallynotdavid/megaloader/releases).

## Three main commands

The CLI provides three commands: `extract` for previewing files, `download` for
downloading them, and `plugins` to list supported platforms.

### extract

Preview what files are available without downloading:

```bash
megaloader extract "https://pixeldrain.com/l/DDGtvvTU"
```

This shows files with their metadata:

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

The extract command is a dry run. It discovers files but doesn't download
anything. This is useful for checking what's available before committing to a
download.

Get structured JSON output instead:

```bash
megaloader extract "https://pixeldrain.com/l/DDGtvvTU" --json
```

This returns machine-readable data:

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

The JSON format is ideal for automation and piping to other tools like `jq`.

Enable debug logging to see what's happening under the hood:

```bash
megaloader extract "https://pixeldrain.com/l/DDGtvvTU" --verbose
```

### download

Download files to a directory:

```bash
megaloader download "https://pixeldrain.com/l/DDGtvvTU" ./my-downloads
```

The output directory is optional and defaults to `./downloads`:

```bash
megaloader download "https://pixeldrain.com/l/DDGtvvTU"
```

You'll see progress bars for each file as they download. By default, files are
organized into subfolders by collection name. Disable this with `--flat`:

```bash
megaloader download "https://pixeldrain.com/l/DDGtvvTU" ./downloads --flat
```

Filter files by pattern to download only what you need:

```bash
# Only JPG files
megaloader download "https://pixeldrain.com/l/DDGtvvTU" ./images --filter "*.jpg"

# Only videos
megaloader download "https://pixeldrain.com/l/DDGtvvTU" ./videos --filter "*.mp4"
```

The filter uses glob patterns, so you can match by filename prefix, suffix, or
any pattern.

Provide a password for protected content:

```bash
megaloader download "https://gofile.io/d/abc123" ./downloads --password "secret"
```

### plugins

List all supported platforms:

```bash
megaloader plugins
```

Output shows domains and their plugin names:

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

This is useful for quickly checking if a platform is supported before trying to
extract from it.

## Global options

These work with all commands:

```bash
megaloader --version      # Show version
megaloader --help         # Show help
megaloader extract --help # Help for specific command
```

## Common workflows

Preview before downloading to verify the URL works and see what's available:

```bash
# Check what's available first
megaloader extract "https://pixeldrain.com/l/DDGtvvTU"

# Looks good? Download it
megaloader download "https://pixeldrain.com/l/DDGtvvTU" ./downloads
```

Check if a platform is supported:

```bash
megaloader plugins | grep pixeldrain
```

Download with custom organization:

```bash
# Organized by collection (default)
megaloader download "https://pixeldrain.com/l/DDGtvvTU" ./downloads

# Everything in one folder
megaloader download "https://pixeldrain.com/l/DDGtvvTU" ./downloads --flat
```

## JSON output for automation

Export metadata to JSON for processing:

```bash
megaloader extract "https://pixeldrain.com/l/DDGtvvTU" --json > metadata.json
```

Process with jq:

```bash
# Count files
megaloader extract --json "https://pixeldrain.com/l/DDGtvvTU" | jq '.count'

# List filenames
megaloader extract --json "https://pixeldrain.com/l/DDGtvvTU" | jq '.items[].filename'

# Calculate total size
megaloader extract --json "https://pixeldrain.com/l/DDGtvvTU" | \
  jq '[.items[].size_bytes] | add'

# Filter for images
megaloader extract --json "https://pixeldrain.com/l/DDGtvvTU" | \
  jq '.items[] | select(.filename | endswith(".jpg") or endswith(".png"))'
```

Extract just the download URLs:

```bash
megaloader extract --json "https://pixeldrain.com/l/DDGtvvTU" | \
  jq -r '.items[].download_url'
```

This is useful for passing URLs to other download tools like wget or curl.

## Filtering downloads

Download specific file types:

```bash
# Only images
megaloader download --filter "*.jpg" "https://pixeldrain.com/l/DDGtvvTU" ./images

# Only videos
megaloader download --filter "*.mp4" "https://pixeldrain.com/l/DDGtvvTU" ./videos
```

Filter by filename pattern:

```bash
# Files starting with "sample"
megaloader download --filter "sample*" "https://pixeldrain.com/l/DDGtvvTU" ./samples

# Files containing "2024"
megaloader download --filter "*2024*" "https://pixeldrain.com/l/DDGtvvTU" ./2024
```

Note that you need to run the command separately for each filter pattern.
Multiple filters aren't yet supported in a single command.

## Authentication

Password-protected GoFile:

```bash
megaloader download --password "secret123" "https://gofile.io/d/abc123" ./downloads
```

Using environment variables:

```bash
export GOFILE_PASSWORD="secret123"
megaloader download "https://gofile.io/d/abc123" ./downloads
```

Command-line password takes precedence over environment variables.

For platforms requiring authentication (Fanbox, Pixiv, Rule34), set the
appropriate environment variables:

```bash
export FANBOX_SESSION_ID="your_cookie"
export PIXIV_SESSION_ID="your_cookie"
export RULE34_API_KEY="your_key"
export RULE34_USER_ID="your_id"

megaloader download "https://creator.fanbox.cc" ./output
```

See the [plugin options reference](/reference/plugin-options) for details on
authentication requirements for each platform.

## Shell integration

Process multiple URLs from a file:

```bash
# urls.txt contains one URL per line
while read url; do
    megaloader download "$url" ./downloads
done < urls.txt
```

Conditional downloads:

```bash
if megaloader extract "https://pixeldrain.com/l/DDGtvvTU"; then
    megaloader download "https://pixeldrain.com/l/DDGtvvTU" ./downloads
else
    echo "Extraction failed"
fi
```

Error handling in scripts:

```bash
#!/bin/bash
set -e

URL="https://pixeldrain.com/l/DDGtvvTU"
OUTPUT="./downloads"

if ! megaloader download "$URL" "$OUTPUT"; then
    echo "Download failed for $URL" >&2
    exit 1
fi

echo "Download completed"
```

Save logs to file:

```bash
megaloader download --verbose "https://pixeldrain.com/l/DDGtvvTU" ./downloads 2>&1 | \
  tee download.log
```

## Custom directory structures

Download to dated directories:

```bash
megaloader download "https://pixeldrain.com/l/DDGtvvTU" ./downloads/$(date +%Y-%m-%d)
```

Platform-specific folders:

```bash
PLATFORM="pixeldrain"
megaloader download "https://pixeldrain.com/l/DDGtvvTU" ./downloads/$PLATFORM
```

## Combining with other tools

Download with wget instead of the built-in downloader:

```bash
megaloader extract --json "https://pixeldrain.com/l/DDGtvvTU" | \
  jq -r '.items[].download_url' | \
  wget -i -
```

Create an archive after downloading:

```bash
megaloader download "https://pixeldrain.com/l/DDGtvvTU" ./temp
tar -czf archive.tar.gz -C ./temp .
rm -rf ./temp
```

Generate a download report:

```bash
megaloader extract --json "https://pixeldrain.com/l/DDGtvvTU" | \
  jq -r '.items[] | "\(.filename)\t\(.size_bytes)\t\(.collection_name)"' > report.tsv
```

## Verification and validation

Check all files were downloaded:

```bash
EXPECTED=$(megaloader extract --json "$URL" | jq '.count')
ACTUAL=$(find ./downloads -type f | wc -l)

if [ "$EXPECTED" -eq "$ACTUAL" ]; then
    echo "All files downloaded"
else
    echo "Warning: Expected $EXPECTED, found $ACTUAL"
fi
```

Retry failed downloads:

```bash
#!/bin/bash
MAX_RETRIES=3
URL="$1"
OUTPUT="$2"

for i in $(seq 1 $MAX_RETRIES); do
    if megaloader download "$URL" "$OUTPUT"; then
        echo "Download successful"
        exit 0
    else
        echo "Attempt $i failed, retrying..."
        sleep 5
    fi
done

echo "Failed after $MAX_RETRIES attempts"
exit 1
```

## Exit codes

The CLI uses standard exit codes:

- `0` = Success
- `1` = Error (extraction failed, unsupported domain, etc.)

This makes shell scripting straightforward. You can check the exit code to
determine if a command succeeded.

## When to use CLI vs library

Use the CLI when you need quick one-off downloads, shell scripting, or just want
to explore what's available on a URL without writing code.

Use the library when you need custom download logic, want to process items
programmatically, or are building an application that integrates extraction
functionality.

The CLI is essentially a convenience wrapper around the core library with
progress bars and organized output.

## Tips

Always test extraction first before downloading to verify the URL works and see
what's available.

Use `--json` for automation since it's easier to parse programmatically than
human-readable output.

Filter early with `--filter` to download only what you need rather than
downloading everything then deleting files.

Use `--verbose` when debugging extraction issues to see detailed logs.

Check available disk space before downloading large collections.

Use environment variables for credentials instead of command-line arguments to
avoid exposing them in shell history.
