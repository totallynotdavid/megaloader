---
title: CLI examples
description: Common workflows and usage patterns for the Megaloader CLI including extraction, filtering, and shell integration.
outline: [2, 3]
prev:
  text: 'Commands'
  link: '/cli/commands'
next:
  text: 'Plugins overview'
  link: '/plugins/'
---

# CLI examples

Common workflows and usage patterns for the Megaloader CLI.

[[toc]]

## Basic workflows

### Preview before downloading

Check what files are available before downloading:

```bash
# Extract metadata first
megaloader extract https://pixeldrain.com/l/abc123

# Review the output, then download
megaloader download https://pixeldrain.com/l/abc123 ./downloads
```

### Quick download

Download files in one command:

```bash
megaloader download https://pixeldrain.com/l/abc123 ./downloads
```

### Check supported platforms

Verify a platform is supported:

```bash
megaloader plugins | grep pixeldrain
```

## Extracting metadata to JSON

### Basic JSON export

Export metadata as JSON for processing:

```bash
megaloader extract --json https://pixeldrain.com/l/abc123 > metadata.json
```

### Process with jq

Use `jq` to process JSON output:

```bash
# Count total files
megaloader extract --json https://pixeldrain.com/l/abc123 | jq '.count'

# List all filenames
megaloader extract --json https://pixeldrain.com/l/abc123 | jq '.items[].filename'

# Get total size in bytes
megaloader extract --json https://pixeldrain.com/l/abc123 | \
  jq '[.items[].size_bytes] | add'

# Filter for images only
megaloader extract --json https://pixeldrain.com/l/abc123 | \
  jq '.items[] | select(.filename | endswith(".jpg") or endswith(".png"))'
```

### Extract download URLs

Get just the download URLs:

```bash
megaloader extract --json https://pixeldrain.com/l/abc123 | \
  jq -r '.items[].download_url'
```

This is useful for passing to other download tools like `wget` or `curl`.

## Filtering downloads

### Download specific file types

Download only images:

```bash
megaloader download --filter "*.jpg" https://pixeldrain.com/l/abc123 ./images
```

Download only videos:

```bash
megaloader download --filter "*.mp4" https://pixeldrain.com/l/abc123 ./videos
```

Download multiple extensions using shell expansion:

```bash
# Download both .jpg and .png files
megaloader download --filter "*.jpg" https://pixeldrain.com/l/abc123 ./images
megaloader download --filter "*.png" https://pixeldrain.com/l/abc123 ./images
```

### Filter by filename pattern

Download files matching a pattern:

```bash
# Download files starting with "photo"
megaloader download --filter "photo*" https://pixeldrain.com/l/abc123 ./photos

# Download files containing "2024"
megaloader download --filter "*2024*" https://pixeldrain.com/l/abc123 ./2024-files
```

## Password-protected content

### Gofile with password

Download password-protected Gofile content:

```bash
megaloader download --password "secret123" https://gofile.io/d/abc123 ./downloads
```

### Using environment variables

Set password via environment variable:

```bash
export GOFILE_PASSWORD="secret123"
megaloader download https://gofile.io/d/abc123 ./downloads
```

Note: Command-line `--password` takes precedence over environment variables.

## Organizing downloads

### Default organization (collections)

By default, files are organized into subfolders by collection:

```bash
megaloader download https://pixeldrain.com/l/abc123 ./downloads
```

Result:

```
downloads/
├── Album 1/
│   ├── photo1.jpg
│   └── photo2.jpg
└── Album 2/
    ├── video1.mp4
    └── video2.mp4
```

### Flat organization

Disable collection subfolders with `--flat`:

```bash
megaloader download --flat https://pixeldrain.com/l/abc123 ./downloads
```

Result:

```
downloads/
├── photo1.jpg
├── photo2.jpg
├── video1.mp4
└── video2.mp4
```

### Custom directory structure

Combine with shell commands for custom organization:

```bash
# Download to dated directory
megaloader download https://pixeldrain.com/l/abc123 ./downloads/$(date +%Y-%m-%d)

# Download to platform-specific directory
PLATFORM="pixeldrain"
megaloader download https://pixeldrain.com/l/abc123 ./downloads/$PLATFORM
```

## Shell integration

### Batch processing multiple URLs

Process multiple URLs from a file:

```bash
# urls.txt contains one URL per line
while read url; do
    megaloader download "$url" ./downloads
done < urls.txt
```

### Conditional downloads

Download only if extraction succeeds:

```bash
if megaloader extract https://pixeldrain.com/l/abc123; then
    megaloader download https://pixeldrain.com/l/abc123 ./downloads
else
    echo "Failed to extract metadata"
fi
```

### Error handling

Handle errors in scripts:

```bash
#!/bin/bash
set -e  # Exit on error

URL="https://pixeldrain.com/l/abc123"
OUTPUT="./downloads"

if ! megaloader download "$URL" "$OUTPUT"; then
    echo "Download failed for $URL" >&2
    exit 1
fi

echo "Download completed successfully"
```

### Logging to file

Save verbose output to a log file:

```bash
megaloader download --verbose https://pixeldrain.com/l/abc123 ./downloads 2>&1 | \
  tee download.log
```

---

## Advanced workflows

### Extract, filter, then download

Use JSON output to filter before downloading:

```bash
# Extract metadata
megaloader extract --json https://pixeldrain.com/l/abc123 > metadata.json

# Analyze with jq
jq '.items[] | select(.size_bytes > 10000000) | .filename' metadata.json

# Download based on analysis
megaloader download https://pixeldrain.com/l/abc123 ./downloads
```

### Download with progress monitoring

Monitor download progress in real-time:

```bash
megaloader download --verbose https://pixeldrain.com/l/abc123 ./downloads
```

The `--verbose` flag shows detailed extraction and download progress.

### Verify downloads

Check if all files were downloaded:

```bash
# Count expected files
EXPECTED=$(megaloader extract --json "$URL" | jq '.count')

# Count downloaded files
ACTUAL=$(find ./downloads -type f | wc -l)

if [ "$EXPECTED" -eq "$ACTUAL" ]; then
    echo "All files downloaded successfully"
else
    echo "Warning: Expected $EXPECTED files, found $ACTUAL"
fi
```

## Platform-specific examples

### PixelDrain lists

Download from PixelDrain list:

```bash
megaloader download https://pixeldrain.com/l/abc123 ./pixeldrain-files
```

### Gofile folders

Download from Gofile folder:

```bash
megaloader download https://gofile.io/d/abc123 ./gofile-files
```

With password:

```bash
megaloader download --password "secret" https://gofile.io/d/abc123 ./gofile-files
```

### Cyberdrop albums

Download from Cyberdrop album:

```bash
megaloader download https://cyberdrop.me/a/abc123 ./cyberdrop-album
```

### Bunkr albums

Download from Bunkr album:

```bash
megaloader download https://bunkr.si/a/abc123 ./bunkr-album
```

## Combining with other tools

### Download with wget

Extract URLs and download with wget:

```bash
megaloader extract --json https://pixeldrain.com/l/abc123 | \
  jq -r '.items[].download_url' | \
  wget -i -
```

### Create download archive

Download and create archive:

```bash
megaloader download https://pixeldrain.com/l/abc123 ./temp-downloads
tar -czf archive.tar.gz -C ./temp-downloads .
rm -rf ./temp-downloads
```

### Generate download report

Create a report of downloaded files:

```bash
megaloader extract --json https://pixeldrain.com/l/abc123 | \
  jq -r '.items[] | "\(.filename)\t\(.size_bytes)\t\(.collection_name)"' > report.tsv
```

### Filter by size

Download only files larger than 1MB:

```bash
# Extract and filter
megaloader extract --json https://pixeldrain.com/l/abc123 | \
  jq '.items[] | select(.size_bytes > 1048576) | .filename'

# Then download (CLI doesn't support size filtering directly)
megaloader download https://pixeldrain.com/l/abc123 ./downloads
```

## Troubleshooting

### Enable verbose logging

See detailed extraction process:

```bash
megaloader extract --verbose https://pixeldrain.com/l/abc123
```

### Check platform support

Verify platform is supported:

```bash
megaloader plugins | grep -i "pixeldrain"
```

### Test extraction first

Always test extraction before downloading:

```bash
# Test first
megaloader extract https://example.com/content

# If successful, download
megaloader download https://example.com/content ./downloads
```

### Handle network issues

Retry failed downloads:

```bash
#!/bin/bash
MAX_RETRIES=3
RETRY=0

while [ $RETRY -lt $MAX_RETRIES ]; do
    if megaloader download "$URL" ./downloads; then
        echo "Download successful"
        break
    else
        RETRY=$((RETRY + 1))
        echo "Retry $RETRY/$MAX_RETRIES"
        sleep 5
    fi
done
```

## Tips and Best Practices

1. **Always test extraction first**: Use `extract` to verify the URL works before downloading
2. **Use `--json` for automation**: JSON output is easier to parse in scripts
3. **Filter early**: Use `--filter` to download only what you need
4. **Organize with collections**: Default collection organization keeps files organized
5. **Use `--verbose` for debugging**: Helps identify issues with extraction or downloads
6. **Check platform support**: Use `megaloader plugins` to verify platform is supported
7. **Handle passwords securely**: Use environment variables instead of command-line arguments for sensitive passwords
8. **Monitor disk space**: Check available space before downloading large collections
