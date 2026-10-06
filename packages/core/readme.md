# megaloader

[![PyPI version](https://badge.fury.io/py/megaloader.svg)](https://badge.fury.io/py/megaloader)
[![CodeQL](https://github.com/totallynotdavid/megaloader/actions/workflows/codeql.yml/badge.svg)](https://github.com/totallynotdavid/megaloader/actions/workflows/codeql.yml)
[![lint and format check](https://github.com/totallynotdavid/megaloader/actions/workflows/checks.yml/badge.svg)](https://github.com/totallynotdavid/megaloader/actions/workflows/checks.yml)
[![codecov](https://codecov.io/gh/totallynotdavid/megaloader/graph/badge.svg?token=SBHAGJJB8L)](https://codecov.io/gh/totallynotdavid/megaloader)

A Python library that lists the downloadable files behind an album, gallery, or
file link on a hosting site. It returns each file's direct URL, filename, and
the headers the download needs. Your code does the downloading.

```bash
pip install megaloader
```

It needs Python 3.10 or newer.

```python
import megaloader as mgl

for item in mgl.extract("https://bunkr.si/a/xYKtNmBx"):
    print(item.filename, item.download_url)
```

`extract()` picks the plugin from the URL's domain and yields `DownloadItem`
objects lazily, so requests happen as you iterate. Failures raise `ValueError`,
`TypeError`, `UnsupportedDomainError`, or `ExtractionError`, which carries a
`category` such as `rate_limit` or `access`.

Plugins cover Bunkr, Cyberdrop, Fapello, GoFile, PixelDrain, Pixiv, Rule34,
Thothub, and Thotslife.

## Learn more

- [Getting started](https://totallynotdavid.github.io/megaloader/getting-started)
- [Library reference](https://totallynotdavid.github.io/megaloader/library)
- [Errors](https://totallynotdavid.github.io/megaloader/errors)
- [Writing plugins](https://totallynotdavid.github.io/megaloader/writing-plugins)
- [Source and contributing](https://github.com/totallynotdavid/megaloader)
