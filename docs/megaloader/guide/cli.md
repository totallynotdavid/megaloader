# CLI

The Megaloader CLI provides terminal access to extraction and downloading. It's
a thin wrapper around the core library with progress tracking and organized
output.

## Installation

::: code-group

```bash [pip]
pip install megaloader
```

```bash [uv]
uv add megaloader
```

:::

Verify it works:

::: code-group

```bash [pip]
megaloader --version
```

```bash [uv]
uv run megaloader --version
```

:::

You can also download pre-built binaries from the
[release page](https://github.com/totallynotdavid/megaloader/releases).

## Commands

The CLI provides `extract` for previewing, `download` for downloading, and
`plugins` to list supported platforms.

### extract

Preview files without downloading:

```bash
megaloader extract "https://pixeldrain.com/l/DDGtvvTU"
```

::: details Output

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

Get structured JSON output for automation:

```bash
megaloader extract "https://pixeldrain.com/l/DDGtvvTU" --json
```

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

JSON output is great for automation and plays nicely with tools like `jq`. You
can read more about that in the
[JSON output for automation](#json-output-for-automation) section.

Enable debug logging to see what's happening under the hood:

```bash
megaloader extract "https://pixeldrain.com/l/DDGtvvTU" --verbose
```

### download

Download files:

```bash
megaloader download "https://pixeldrain.com/l/DDGtvvTU" ./my-downloads
```

The output directory defaults to `./downloads`:

```bash
megaloader download "https://pixeldrain.com/l/DDGtvvTU"
```

By default, files are organized into subfolders by collection name. Use `--flat`
to disable this:

```bash
megaloader download "https://pixeldrain.com/l/DDGtvvTU" ./downloads --flat
```

Filter files by pattern:

```bash
# Only JPG files
megaloader download "https://pixeldrain.com/l/DDGtvvTU" ./images --filter "*.jpg"

# Only MP4 videos
megaloader download "https://pixeldrain.com/l/DDGtvvTU" ./videos --filter "*.mp4"
```

The filter uses glob patterns, so you can match by filename prefix, suffix, or
any pattern.

Provide a password for protected content:

```bash
megaloader download "https://gofile.io/d/abc123" ./downloads --password "secret"
```

### plugins

List supported platforms:

```bash
megaloader plugins
```

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

## Global options

These work with all commands:

```bash
megaloader --version        # Show version
megaloader --help           # Show help
megaloader extract --help   # Help for specific command
```

## Common workflows

**Preview** before downloading:

1. Check what's available first:

   ```bash
   megaloader extract "https://pixeldrain.com/l/DDGtvvTU"
   ```

2. Looks good? Download it

   ```bash
   megaloader download "https://pixeldrain.com/l/DDGtvvTU" ./downloads
   ```

**Check** platform support:

::: code-group

```bash [bash]
megaloader plugins | grep pixeldrain
```

```powershell [powershell]
megaloader plugins | Select-String pixeldrain
```

:::

Custom **organization**:

```bash
# Organized by collection (default)
megaloader download "https://pixeldrain.com/l/DDGtvvTU" ./downloads

# Everything in one folder
megaloader download "https://pixeldrain.com/l/DDGtvvTU" ./downloads --flat
```

For advanced automation workflows including JSON processing with jq, shell
scripting patterns, and integration with external tools, see
[CLI automation](cli-automation).

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
megaloader download --filter "sample*" "https://pixeldrain.com/l/DDGtvvTU" ./sample

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

::: code-group

```bash [bash]
export GOFILE_PASSWORD="secret123"
megaloader download "https://gofile.io/d/abc123" ./downloads
```

```powershell [powershell]
$Env:GOFILE_PASSWORD = "secret123"
megaloader download "https://gofile.io/d/abc123" ./downloads
```

:::

Command-line takes precedence over environment variables.

For platforms requiring authentication:

::: code-group

```bash [bash]
export FANBOX_SESSION_ID="your_cookie"
export PIXIV_SESSION_ID="your_cookie"
export RULE34_API_KEY="your_key"
export RULE34_USER_ID="your_id"

megaloader download "https://creator.fanbox.cc" ./output
```

```powershell [powershell]
$Env:FANBOX_SESSION_ID = "your_cookie"
$Env:PIXIV_SESSION_ID  = "your_cookie"
$Env:RULE34_API_KEY    = "your_key"
$Env:RULE34_USER_ID    = "your_id"

megaloader download "https://creator.fanbox.cc" ./output
```

:::

See the [plugin options](/reference/options) reference for authentication
details.

## When to use CLI vs library

Use the CLI for quick downloads, shell scripting, or exploring URLs without
writing code.

Use the library when you need custom download logic, programmatic processing, or
application integration.

The CLI is a convenience wrapper around the core library with progress bars and
organized output.
