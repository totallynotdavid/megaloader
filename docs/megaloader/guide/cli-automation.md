# CLI automation

This guide covers advanced automation workflows for power users integrating
megaloader with shell scripts and external tools.

## JSON output

Export metadata for programmatic processing:

::: code-group

```bash [bash]
megaloader extract "https://pixeldrain.com/l/DDGtvvTU" --json > metadata.json
```

```powershell [powershell]
megaloader extract "https://pixeldrain.com/l/DDGtvvTU" --json | Out-File -FilePath metadata.json -Encoding utf8
```

:::

The JSON structure includes source URL, file count, and an array of items with
all metadata fields:

::: details Output

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

:::

## Processing with jq

Count files:

```bash
megaloader extract --json "https://pixeldrain.com/l/DDGtvvTU" | jq '.count'
```

List filenames:

```bash
megaloader extract --json "https://pixeldrain.com/l/DDGtvvTU" | \
  jq '.items[].filename'
```

Calculate total size:

```bash
megaloader extract --json "https://pixeldrain.com/l/DDGtvvTU" | \
  jq '[.items[].size_bytes] | add'
```

Filter for images:

```bash
megaloader extract --json "https://pixeldrain.com/l/DDGtvvTU" | \
  jq '.items[] | select(.filename | endswith(".jpg") or endswith(".png"))'
```

Extract download URLs:

```bash
megaloader extract --json "https://pixeldrain.com/l/DDGtvvTU" | \
  jq -r '.items[].download_url'
```

## Shell integration

Process multiple URLs from a file:

::: code-group

```bash [bash]
# urls.txt contains one URL per line
while read url; do
    megaloader download "$url" ./downloads
done < urls.txt
```

```powershell [powershell]
# urls.txt contains one URL per line
Get-Content urls.txt | ForEach-Object {
    megaloader download $_ ./downloads
}
```

:::

Conditional downloads:

::: code-group

```bash [bash]
if megaloader extract "https://pixeldrain.com/l/DDGtvvTU"; then
    megaloader download "https://pixeldrain.com/l/DDGtvvTU" ./downloads
else
    echo "Extraction failed"
fi
```

```powershell [powershell]
if ($LASTEXITCODE -eq 0 -and (megaloader extract "https://pixeldrain.com/l/DDGtvvTU")) {
    megaloader download "https://pixeldrain.com/l/DDGtvvTU" ./downloads
} else {
    Write-Output "Extraction failed"
}
```

:::

Error handling in scripts:

::: code-group

```bash [bash]
#!/bin/bash
set -e

URL="https://pixeldrain.com/l/DDGtvvTU"
OUTPUT="./downloads"

if ! megaloader download "$URL" "$OUTPUT"; then
    echo "Download failed for $URL" >&2
    exit 1
fi
```

```powershell [powershell]
$ErrorActionPreference = "Stop"

$URL = "https://pixeldrain.com/l/DDGtvvTU"
$OUTPUT = "./downloads"

megaloader download $URL $OUTPUT
if ($LASTEXITCODE -ne 0) {
    Write-Error "Download failed for $URL"
    exit 1
}
```

:::

Save logs to a file:

::: code-group

```bash [bash]
megaloader download --verbose "https://pixeldrain.com/l/DDGtvvTU" ./downloads 2>&1 | \
  tee download.log
```

```powershell [powershell]
megaloader download --verbose "https://pixeldrain.com/l/DDGtvvTU" ./downloads 2>&1 | \
  Tee-Object -FilePath download.log
```

:::

## Combining with other tools

Download with wget/curl instead of the built-in downloader:

::: code-group

```bash [bash]
megaloader extract --json "https://pixeldrain.com/l/DDGtvvTU" | \
  jq -r '.items[].download_url' | \
  wget -i -
```

```powershell [powershell]
megaloader extract --json "https://pixeldrain.com/l/DDGtvvTU" | \
  jq -r '.items[].download_url' | \
  ForEach-Object { curl.exe -O $_ }
```

:::

Create an archive after downloading:

::: code-group

```bash [bash]
megaloader download "https://pixeldrain.com/l/DDGtvvTU" ./temp
tar -czf archive.tar.gz -C ./temp .
```

```powershell [powershell]
megaloader download "https://pixeldrain.com/l/DDGtvvTU" ./temp
Compress-Archive -Path ./temp/* -DestinationPath archive.zip
```

:::

Generate a download report:

::: code-group

```bash [bash]
megaloader extract --json "https://pixeldrain.com/l/DDGtvvTU" | \
  jq -r '.items[] | "\(.filename)\t\(.size_bytes)\t\(.collection_name)"' > report.tsv
```

```powershell [powershell]
megaloader extract --json "https://pixeldrain.com/l/DDGtvvTU" | \
  jq -r '.items[] | "\(.filename)\t\(.size_bytes)\t\(.collection_name)"' | \
  Out-File -FilePath report.tsv -Encoding utf8
```

:::

## Exit codes

The CLI uses standard exit codes for reliable scripting:

- `0` = Success
- `1` = Error (extraction failed, unsupported domain, etc.)

Example:

::: code-group

```bash [bash]
if megaloader extract "$URL"; then
    echo "Success"
else
    echo "Failed"
    exit 1
fi
```

```powershell [powershell]
megaloader extract $URL
if ($LASTEXITCODE -eq 0) {
    Write-Output "Success"
} else {
    Write-Output "Failed"
    exit 1
}
```

:::
