# [monorepo]: megaloader

<img src="assets/logo.svg" alt="Megaloader Logo" width="100">

[![CodeQL](https://github.com/totallynotdavid/megaloader/actions/workflows/codeql.yml/badge.svg)](https://github.com/totallynotdavid/megaloader/actions/workflows/codeql.yml)
[![lint and format check](https://github.com/totallynotdavid/megaloader/actions/workflows/checks.yml/badge.svg)](https://github.com/totallynotdavid/megaloader/actions/workflows/checks.yml)
[![codecov](https://codecov.io/gh/totallynotdavid/megaloader/graph/badge.svg?token=SBHAGJJB8L)](https://codecov.io/gh/totallynotdavid/megaloader)

Python library and CLI for extracting downloadable content from file hosting
platforms. Supports 11 platforms through a plugin architecture with automatic
URL detection.

Megaloader is available as two independent packages:

```bash
pip install megaloader          # core library
pip install megaloader-cli      # terminal CLI
```

Install one or both depending on whether you need API integration, command-line
tools, or both.

## Usage

Library usage:

```python
from megaloader import extract

for item in extract("https://pixeldrain.com/l/abc123"):
    print(f"{item.filename} - {item.download_url}")
```

CLI usage:

```bash
megaloader download https://pixeldrain.com/l/abc123
```

More detailed information is available in the package-specific documentation:

- Core library: [packages/core/readme.md](packages/core/readme.md)
- CLI: [packages/cli/readme.md](packages/cli/readme.md)

## Supported platforms

The library supports four core platforms with active maintenance and seven
extended platforms on best-effort basis. Core platforms receive priority for bug
fixes and feature development. Extended platforms work as of November 2025 but
may break without immediate fixes.

| Platform    | Domains                | Supports                                      | Status   |
| ----------- | ---------------------- | --------------------------------------------- | -------- |
| Bunkr       | bunkr.{si,la,is,ru,su} | Albums, single files                          | Core     |
| PixelDrain  | pixeldrain.com         | Lists, files, proxy support                   | Core     |
| Cyberdrop   | cyberdrop.{me,to,cr}   | Albums, single files                          | Core     |
| GoFile      | gofile.io              | Folders (including password-protected), files | Core     |
| Fanbox      | {creator}.fanbox.cc    | Creator content, authentication               | Extended |
| Pixiv       | pixiv.net              | Artworks, galleries, authentication           | Extended |
| Rule34      | rule34.xxx             | Tags, posts, API                              | Extended |
| ThotsLife   | thotslife.com          | Albums, posts                                 | Extended |
| ThotHub.VIP | thothub.vip            | Videos, albums                                | Extended |
| ThotHub.TO  | thothub.to             | Videos, albums                                | Extended |
| Fapello     | fapello.com            | Model profiles                                | Extended |

Additional notes on authentication and platform-specific features are documented
in the core library's [readme](packages/core/readme.md).

## Development

This monorepo uses a uv workspace. The core library is in
[`packages/core/`](packages/core/) and the CLI tool is in
[`packages/cli/`](packages/cli/). Each one is published to PyPI as a separate
package.

The repository is organized like this:

```
megaloader/
├── apps/
│   ├── api/        # FastAPI server (deployed to Vercel)
│   └── docs/       # VitePress site (deployed to GitHub Pages)
├── packages/
│   ├── core/       # megaloader, the core library
│   └── cli/        # megaloader-cli, the command-line interface
├── scripts/        # Development utilities
└── assets/         # Static files
```

To set up a development environment, clone the repository and install all
workspace dependencies:

```bash
git clone https://github.com/totallynotdavid/megaloader
cd megaloader
uv sync
```

If you prefer to manage tools with mise, run:

```bash
mise install
mise run sync
```

This installs the toolchain versions defined in [`mise.toml`](mise.toml).

Before submitting changes, run the formatters, linters, and tests:

```bash
uv run ruff format .        # mise run format
uv run ruff check --fix .   # mise run format
uv run mypy packages/core   # mise run mypy
uv run pytest               # mise run test, mise run test-unit
```

These commands format the code, fix lint issues, check types, and run the test
suite.

See [.github/CONTRIBUTING.md](.github/CONTRIBUTING.md) for plugin development
guidelines.

## Project history

Originally created by [@Ximaz](https://github.com/Ximaz) before 2023. The
repository was later deleted or made private. Current maintainer
[@totallynotdavid](https://github.com/totallynotdavid) rebuilt the codebase from
scratch to fix platform changes and modernize the architecture.

Feature discussions and issue reports take place on
[GitHub Discussions](https://github.com/totallynotdavid/megaloader/discussions).
