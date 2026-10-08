# Megaloader

[![CodeQL](https://github.com/totallynotdavid/megaloader/actions/workflows/codeql.yml/badge.svg)](https://github.com/totallynotdavid/megaloader/actions/workflows/codeql.yml)
[![lint and format check](https://github.com/totallynotdavid/megaloader/actions/workflows/checks.yml/badge.svg)](https://github.com/totallynotdavid/megaloader/actions/workflows/checks.yml)

Megaloader finds the files behind an album, gallery, or file link on a hosting
site. It is for shell users and Python programs that need file metadata. The
library returns direct URLs, filenames, and required download headers; it does
not transfer files. The CLI also downloads them.

Install the CLI:

```bash
pip install megaloader-cli
```

List the files behind a link:

```console
$ megaloader extract https://bunkr.si/a/xYKtNmBx
✓ Using plugin: Bunkr
Extracting metadata... ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Found 6 files:

  01. sample-image-06.jpg
  02. sample-image-04.jpg
  03. sample-image-05.jpg
  04. sample-image-03.jpg
  05. sample-image-01.jpg
  06. sample-image-02.jpg
```

Install the library when your program will handle the transfer:

```bash
pip install megaloader
```

```python
import megaloader as mgl

for item in mgl.extract("https://bunkr.si/a/xYKtNmBx"):
    print(item.filename, item.download_url)
```

Megaloader supports Python 3.10 and newer.

## Features

- `extract()` selects a plugin from the URL and yields `DownloadItem` objects
  lazily.
- Each item carries its filename, direct URL, collection name, optional size,
  and the headers its download needs.
- `megaloader download` saves collections into folders, filters by filename, and
  skips files that already exist.
- `megaloader extract --json` emits item metadata for scripts.
- `ExtractionError` classifies failures as `request`, `auth`, `access`,
  `network`, `timeout`, `protocol`, `rate_limit`, or `unknown`.
- Plugins send every request through the fetcher supplied by `extract()`, so
  they can be tested with recorded responses.
- The FastAPI service exposes extraction and downloads over HTTP.

See the [manual](https://totallynotdavid.github.io/megaloader) for supported
platforms, library and CLI reference, and plugin authoring.

Contributors can start with
[`.github/CONTRIBUTING.md`](.github/CONTRIBUTING.md). The
[architecture map](docs/architecture.md) describes the code boundaries.

## License

Apache-2.0. See [LICENSE](LICENSE).
