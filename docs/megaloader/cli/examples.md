---
title: CLI examples
description: Common workflows and patterns for using the CLI effectively
outline: [2, 3]
prev:
  text: "CLI usage"
  link: "/cli/usage"
next:
  text: "Plugins overview"
  link: "/plugins/"
---

# CLI examples

Practical workflows and patterns for getting the most out of the CLI.

## Basic workflows

Preview before downloading:

```bash
# Check what's available first
megaloader extract "https://pixeldrain.com/l/abc123"

# Looks good? Download it
megaloader download "https://pixeldrain.com/l/abc123" ./downloads
```

Check if a platform is supported:

```bash
megaloader plugins | grep pixeldrain
```

Download with custom organization:

```bash
# Organized by collection (default)
megaloader download "https://pixeldrain.com/l/abc123" ./downloads

# Everything in one folder
megaloader download "https://pixeldrain.com/l/abc123" ./downloads --flat
```

## JSON output for automation

Export metadata to JSON:

```bash
megaloader extract "https://pixeldrain.com/l/abc123" --json > metadata.json
```

Process with jq:

```bash
# Count files
megaloader extract --json "https://pixeldrain.com/l/abc123" | jq '.count'

# List filenames
megaloader extract --json "https://pixeldrain.com/l/abc123" | jq '.items[].filename'

# Calculate total size
megaloader extract --json "https://pixeldrain.com/l/abc123" | \
  jq '[.items[].size_bytes] | add'

# Filter for images
megaloader extract --json "https://pixeldrain.com/l/abc123" | \
  jq '.items[] | select(.filename | endswith(".jpg") or endswith(".png"))'
```

Extract just the download URLs:

```bash
megaloader extract --json "https://pixeldrain.com/l/abc123" | \
  jq -r '.items[].download_url'
```

Useful for passing to other download tools like wget or curl.

## Filtering downloads

Download specific file types:

```bash
# Only images
megaloader download --filter "*.jpg" "https://pixeldrain.com/l/abc123" ./images

# Only videos
megaloader download --filter "*.mp4" "https://pixeldrain.com/l/abc123" ./videos

# Multiple filters (run separately)
megaloader download --filter "*.jpg" "https://pixeldrain.com/l/abc123" ./media
megaloader download --filter "*.png" "https://pixeldrain.com/l/abc123" ./media
```

Filter by filename pattern:

```bash
# Files starting with "photo"
megaloader download --filter "photo*" "https://pixeldrain.com/l/abc123" ./photos

# Files containing "2024"
megaloader download --filter "*2024*" "https://pixeldrain.com/l/abc123" ./2024
```

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
if megaloader extract "https://pixeldrain.com/l/abc123"; then
    megaloader download "https://pixeldrain.com/l/abc123" ./downloads
else
    echo "Extraction failed"
fi
```

Error handling in scripts:

```bash
#!/bin/bash
set -e

URL="https://pixeldrain.com/l/abc123"
OUTPUT="./downloads"

if ! megaloader download "$URL" "$OUTPUT"; then
    echo "Download failed for $URL" >&2
    exit 1
fi

echo "Download completed"
```

Save logs to file:

```bash
megaloader download --verbose "https://pixeldrain.com/l/abc123" ./downloads 2>&1 | \
  tee download.log
```

## Custom directory structures

Download to dated directories:

```bash
megaloader download "https://pixeldrain.com/l/abc123" ./downloads/$(date +%Y-%m-%d)
```

Platform-specific folders:

```bash
PLATFORM="pixeldrain"
megaloader download "https://pixeldrain.com/l/abc123" ./downloads/$PLATFORM
```

## Combining with other tools

Download with wget instead:

```bash
megaloader extract --json "https://pixeldrain.com/l/abc123" | \
  jq -r '.items[].download_url' | \
  wget -i -
```

Create an archive after downloading:

```bash
megaloader download "https://pixeldrain.com/l/abc123" ./temp
tar -czf archive.tar.gz -C ./temp .
rm -rf ./temp
```

Generate a download report:

```bash
megaloader extract --json "https://pixeldrain.com/l/abc123" | \
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

## Platform-specific examples

PixelDrain lists:

```bash
megaloader download "https://pixeldrain.com/l/abc123" ./pixeldrain
```

GoFile with password:

```bash
megaloader download --password "secret" "https://gofile.io/d/abc123" ./gofile
```

Cyberdrop albums:

```bash
megaloader download "https://cyberdrop.me/a/abc123" ./cyberdrop
```

Bunkr albums:

```bash
megaloader download "https://bunkr.si/a/abc123" ./bunkr
```

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
