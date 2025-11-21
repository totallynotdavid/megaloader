# CLI Examples

Common workflows and usage patterns for the Megaloader CLI.

## Basic Workflows

### Preview Before Downloading

Check what files are available before downloading:

```bash
# Extract metadata first
megaloader extract https://pixeldrain.com/l/abc123

# Review the output, then download
megaloader download https://pixeldrain.com/l/abc123 ./downloads
```

### Quick Download

Download files in one command:

```bash
megaloader download https://pixeldrain.com/l/abc123 ./downloads
```

### Check Supported Platforms

Verify a platform is supported:

```bash
megaloader plugins | grep pixeldrain
```

---

## Extracting Metadata to JSON

### Basic JSON Export

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

### Extract Download URLs

Get just the download URLs:

```bash
megaloader extract --json https://pixeldrain.com/l/abc123 | \
  jq -r '.items[].download_url'
```

This is useful for passing to other download tools like `wget` or `curl`.

---

## Filtering Downloads

### Download Specific File Types

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

### Filter by Filename Pattern

Download files matching a pattern:

```bash
# Download files starting with "photo"
megaloader download --filter "photo*" https://pixeldrain.com/l/abc123 ./photos

# Download files containing "2024"
megaloader download --filter "*2024*" https://pixeldrain.com/l/abc123 ./2024-files
```

---

## Password-Protected Content

### Gofile with Password

Download password-protected Gofile content:

```bash
megaloader download --password "secret123" https://gofile.io/d/abc123 ./downloads
```

### Using Environment Variables

Set password via environment variable:

```bash
export GOFILE_PASSWORD="secret123"
megaloader download https://gofile.io/d/abc123 ./downloads
```

Note: Command-line `--password` takes precedence over environment variables.

---

## Organizing Downloads

### Default Organization (Collections)

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

### Flat Organization

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

### Custom Directory Structure

Combine with shell commands for custom organization:

```bash
# Download to dated directory
megaloader download https://pixeldrain.com/l/abc123 ./downloads/$(date +%Y-%m-%d)

# Download to platform-specific directory
PLATFORM="pixeldrain"
megaloader download https://pixeldrain.com/l/abc123 ./downloads/$PLATFORM
```

---

## Shell Integration

### Batch Processing Multiple URLs

Process multiple URLs from a file:

```bash
# urls.txt contains one URL per line
while read url; do
    megaloader download "$url" ./downloads
done < urls.txt
```

### Conditional Downloads

Download only if extraction succeeds:

```bash
if megaloader extract https://pixeldrain.com/l/abc123; then
    megaloader download https://pixeldrain.com/l/abc123 ./downloads
else
    echo "Failed to extract metadata"
fi
```

### Error Handling

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

### Logging to File

Save verbose output to a log file:

```bash
megaloader download --verbose https://pixeldrain.com/l/abc123 ./downloads 2>&1 | \
  tee download.log
```

---

## Advanced Workflows

### Extract, Filter, Then Download

Use JSON output to filter before downloading:

```bash
# Extract metadata
megaloader extract --json https://pixeldrain.com/l/abc123 > metadata.json

# Analyze with jq
jq '.items[] | select(.size_bytes > 10000000) | .filename' metadata.json

# Download based on analysis
megaloader download https://pixeldrain.com/l/abc123 ./downloads
```

### Download with Progress Monitoring

Monitor download progress in real-time:

```bash
megaloader download --verbose https://pixeldrain.com/l/abc123 ./downloads
```

The `--verbose` flag shows detailed extraction and download progress.

### Verify Downloads

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

---

## Platform-Specific Examples

### PixelDrain Lists

Download from PixelDrain list:

```bash
megaloader download https://pixeldrain.com/l/abc123 ./pixeldrain-files
```

### Gofile Folders

Download from Gofile folder:

```bash
megaloader download https://gofile.io/d/abc123 ./gofile-files
```

With password:

```bash
megaloader download --password "secret" https://gofile.io/d/abc123 ./gofile-files
```

### Cyberdrop Albums

Download from Cyberdrop album:

```bash
megaloader download https://cyberdrop.me/a/abc123 ./cyberdrop-album
```

### Bunkr Albums

Download from Bunkr album:

```bash
megaloader download https://bunkr.si/a/abc123 ./bunkr-album
```

---

## Combining with Other Tools

### Download with wget

Extract URLs and download with wget:

```bash
megaloader extract --json https://pixeldrain.com/l/abc123 | \
  jq -r '.items[].download_url' | \
  wget -i -
```

### Create Download Archive

Download and create archive:

```bash
megaloader download https://pixeldrain.com/l/abc123 ./temp-downloads
tar -czf archive.tar.gz -C ./temp-downloads .
rm -rf ./temp-downloads
```

### Generate Download Report

Create a report of downloaded files:

```bash
megaloader extract --json https://pixeldrain.com/l/abc123 | \
  jq -r '.items[] | "\(.filename)\t\(.size_bytes)\t\(.collection_name)"' > report.tsv
```

### Filter by Size

Download only files larger than 1MB:

```bash
# Extract and filter
megaloader extract --json https://pixeldrain.com/l/abc123 | \
  jq '.items[] | select(.size_bytes > 1048576) | .filename'

# Then download (CLI doesn't support size filtering directly)
megaloader download https://pixeldrain.com/l/abc123 ./downloads
```

---

## Troubleshooting

### Enable Verbose Logging

See detailed extraction process:

```bash
megaloader extract --verbose https://pixeldrain.com/l/abc123
```

### Check Platform Support

Verify platform is supported:

```bash
megaloader plugins | grep -i "pixeldrain"
```

### Test Extraction First

Always test extraction before downloading:

```bash
# Test first
megaloader extract https://example.com/content

# If successful, download
megaloader download https://example.com/content ./downloads
```

### Handle Network Issues

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

---

## Tips and Best Practices

1. **Always test extraction first**: Use `extract` to verify the URL works before downloading
2. **Use `--json` for automation**: JSON output is easier to parse in scripts
3. **Filter early**: Use `--filter` to download only what you need
4. **Organize with collections**: Default collection organization keeps files organized
5. **Use `--verbose` for debugging**: Helps identify issues with extraction or downloads
6. **Check platform support**: Use `megaloader plugins` to verify platform is supported
7. **Handle passwords securely**: Use environment variables instead of command-line arguments for sensitive passwords
8. **Monitor disk space**: Check available space before downloading large collections

---

## Next Steps

- See [Commands](/cli/commands) for complete command reference
- See [Core Library](/core/overview) for programmatic usage
- See [Plugin Options](/plugins/plugin-options) for platform-specific authentication
