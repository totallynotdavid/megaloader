# Command line

The `megaloader` command extracts file metadata and downloads files. It comes
from the `megaloader-cli` package.

```bash
pip install megaloader-cli
```

```console
$ megaloader --version
megaloader, version 0.2.0
```

Each CLI [release](https://github.com/totallynotdavid/megaloader/releases) also
attaches single-file binaries, `megaloader-cli-linux` and
`megaloader-cli-windows.exe`, that need no Python.

## Commands

| Command                                | Does                                                         |
| -------------------------------------- | ------------------------------------------------------------ |
| `megaloader extract URL`               | Lists the files a URL holds. Downloads none.                 |
| `megaloader download URL [OUTPUT_DIR]` | Downloads the files. `OUTPUT_DIR` defaults to `./downloads`. |
| `megaloader plugins`                   | Lists the supported domains.                                 |

## List files

```console
$ megaloader extract https://pixeldrain.com/l/GSLKgrYj
✓ Using plugin: PixelDrain
Extracting metadata... ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Found 6 files:

  01. sample-image-06.jpg
      Size: 0.08 MB
  02. sample-image-04.jpg
      Size: 0.39 MB
  03. sample-image-05.jpg
      Size: 0.19 MB
  04. sample-image-03.jpg
      Size: 0.27 MB
  05. sample-image-01.jpg
      Size: 0.20 MB
  06. sample-image-02.jpg
      Size: 0.39 MB
```

A `Collection:` line appears under a file when the platform names the album it
belongs to. A `Size:` line appears when the platform reports the size.

### JSON output

`--json` prints one document and no progress or plugin line, so it is safe to
pipe:

```console
$ megaloader extract https://bunkr.si/a/xYKtNmBx --json
{
  "source": "https://bunkr.si/a/xYKtNmBx",
  "count": 6,
  "items": [
    {
      "download_url": "https://c1mp-b.cdn.cr/3e48b142-bc3b-4b8d-bbc9-db9f891687d3.jpg?n=sample-image-06.jpg",
      "filename": "sample-image-06.jpg",
      "collection_name": null,
      "source_id": "55418273",
      "headers": {
        "Referer": "https://get.bunkrr.su/"
      },
      "size_bytes": null
    },
    ...
  ]
}
```

`source` is the URL you passed. Each entry in `items` has the fields of a
[`DownloadItem`](library#downloaditem). [Scripting the CLI](cli-scripting) has
`jq` recipes.

## Download files

```console
$ megaloader download https://pixeldrain.com/l/GSLKgrYj downloads
✓ Using plugin: PixelDrain
Discovering files... ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Found 6 files.
Batch ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% • 6/6 bytes • 256 bytes/s • 0:00:00

✓ Success! Downloaded 6 files.
Location: /home/you/downloads
```

The `Batch` line counts files finished out of files found, but it labels the
count `bytes` (`6/6 bytes` is six files of six). The rate is likewise files per
second shown as `bytes/s`. Each file also gets its own bar, and that bar counts
real bytes.

By default the files of a collection go into a subfolder named for the
collection. Files without a collection go straight into `OUTPUT_DIR`. Folder and
file names have `< > : " / \ | ? *` replaced by `_`.

| Option          | Effect                                                         |
| --------------- | -------------------------------------------------------------- |
| `--flat`        | Put every file in `OUTPUT_DIR`, with no collection subfolders. |
| `--filter GLOB` | Download only filenames that match the glob.                   |
| `-v`            | Log debug output.                                              |
| `--password`    | Password for a protected GoFile folder.                        |
| `--token`       | GoFile API token.                                              |

### Filter by name

`--filter` matches the filename with Python's `fnmatch`. It supports `*`, `?`,
and `[seq]`. It does not support `{jpg,png}` alternatives, so run the command
once per extension:

```console
$ megaloader download https://pixeldrain.com/l/GSLKgrYj images --filter "*-0[12].jpg" --flat
✓ Using plugin: PixelDrain
Discovering files... ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Filtered: 6 → 2 files
✓ Found 2 files.
Batch ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% • 2/2 bytes • 235 bytes/s • 0:00:00

✓ Success! Downloaded 2 files.
Location: /home/you/images
```

### Run it again

A file that already exists at its destination is skipped, so running the same
command again finishes what a failed run left:

```console
$ megaloader download https://pixeldrain.com/l/GSLKgrYj images --filter "*-0[12].jpg" --flat
✓ Using plugin: PixelDrain
Discovering files... ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Filtered: 6 → 2 files
✓ Found 2 files.
⊙ Skipped (exists): sample-image-01.jpg
⊙ Skipped (exists): sample-image-02.jpg
Batch ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% • 2/2 bytes • 1.9 kB/s • 0:00:00

✓ Success! Downloaded 2 files.
```

The summary counts skipped files. A file that fails to download is deleted, and
the command prints `Completed with errors.` and exits with status 1. A run you
interrupt with Ctrl-C leaves its current file partial, and the next run skips
it. Delete that file to fetch it again.

Each download sends a browser `User-Agent` plus the headers the plugin reports
for the item, and times out after 60 seconds.

## Options for platforms

`--password` and `--token` map to the GoFile options of the same names. The
other platform options have no flag. Set them in the environment:

```bash
export PIXIV_PHPSESSID="your_session_cookie"
megaloader download https://www.pixiv.net/en/artworks/123456 pixiv
```

[Plugin options](plugin-options) lists them all.

## Supported domains

```console
$ megaloader plugins

Supported Platforms:

  • bunkr.ax             (Bunkr)
  • bunkr.black          (Bunkr)
  • bunkr.fi             (Bunkr)
  • bunkr.is             (Bunkr)
  • bunkr.la             (Bunkr)
  • bunkr.ru             (Bunkr)
  • bunkr.si             (Bunkr)
  • bunkr.su             (Bunkr)
  • cyberdrop.cr         (Cyberdrop)
  • cyberdrop.me         (Cyberdrop)
  • cyberdrop.to         (Cyberdrop)
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

## Errors

A failure prints one line and exits with status 1:

```console
$ megaloader extract https://unknown.example/x
Extracting metadata... ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Error: No plugin found for domain: unknown.example
$ echo $?
1
```

```console
$ megaloader extract https://bunkr.si/a/doesnotexist1
✓ Using plugin: Bunkr
Extracting metadata... ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Error: bunkr request failed (404): https://bunkr.si/a/doesnotexist1
```

Add `-v` to see the debug log. [Errors](errors) explains the categories.
