# Megaloader

<img src="https://raw.githubusercontent.com/totallynotdavid/megaloader/main/apps/docs/megaloader/public/logo.svg" alt="Megaloader logo" width="100">

[![CodeQL](https://github.com/totallynotdavid/megaloader/actions/workflows/codeql.yml/badge.svg)](https://github.com/totallynotdavid/megaloader/actions/workflows/codeql.yml)
[![lint and format check](https://github.com/totallynotdavid/megaloader/actions/workflows/checks.yml/badge.svg)](https://github.com/totallynotdavid/megaloader/actions/workflows/checks.yml)
[![codecov](https://codecov.io/gh/totallynotdavid/megaloader/graph/badge.svg?token=SBHAGJJB8L)](https://codecov.io/gh/totallynotdavid/megaloader)

Megaloader finds the files behind an album, gallery, or file link on a hosting
site, and downloads them. It is a command-line tool and a Python library with
plugins for the platforms below. The library lists files and the headers each
download needs. It leaves the transfer to your code. The CLI does the transfer.

```console
$ pip install megaloader-cli
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
$ megaloader download https://bunkr.si/a/xYKtNmBx images
```

The library needs Python 3.10 or newer:

```bash
pip install megaloader
```

```python
import megaloader as mgl

for item in mgl.extract("https://bunkr.si/a/xYKtNmBx"):
    print(item.filename, item.download_url)
```

## Features

- One call for every platform. `extract()` picks the plugin from the URL's
  domain and yields `DownloadItem` objects as it finds them.
- Each item carries its filename, direct URL, collection name, size when the
  platform reports it, and the headers the download must send.
- `megaloader download` saves collections into folders, filters by filename, and
  skips files that already exist.
- `megaloader extract --json` prints the items for scripts.
- Failures are typed. `ExtractionError` has a category: `rate_limit`, `auth`,
  `access`, `request`, `network`, `timeout`, `protocol`, or `unknown`.
- Plugins make no network calls of their own. They send requests through a
  fetcher, so tests run a plugin against recorded responses.
- A FastAPI server wraps the library as an HTTP service.

## Platforms

| Platform   | Domains                                        |
| ---------- | ---------------------------------------------- |
| Bunkr      | bunkr.ax, .black, .fi, .is, .la, .ru, .si, .su |
| Cyberdrop  | cyberdrop.cr, .me, .to                         |
| Fapello    | fapello.com                                    |
| GoFile     | gofile.io                                      |
| PixelDrain | pixeldrain.com                                 |
| Pixiv      | pixiv.net                                      |
| Rule34     | rule34.xxx                                     |
| Thothub    | thothub.ch, thothub.to, thothub.vip            |
| Thotslife  | thotslife.com                                  |

## Documentation

The [manual](https://totallynotdavid.github.io/megaloader) covers the library,
the command line, and writing plugins. Its source is in
[`apps/docs/megaloader/`](apps/docs/megaloader/readme.md).

## Contributing

[`.github/CONTRIBUTING.md`](.github/CONTRIBUTING.md) explains how to set up,
test, and submit a change. [`architecture.md`](architecture.md) maps the code.

## License

Apache-2.0. See [LICENSE](LICENSE).
