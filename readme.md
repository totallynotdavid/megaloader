# [monorepo]: megaloader

<img src="logo.png" alt="Megaloader Logo" width="200">

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
in the core library readme.

## Development

This monorepo uses uv workspaces. The core library lives in
[`packages/core/`](packages/core/) and the CLI in
[`packages/cli/`](packages/cli/). Both are published independently to PyPI.
Development tools are configured at the root.

Clone the repository and install dependencies:

```bash
git clone https://github.com/totallynotdavid/megaloader
cd megaloader
uv sync
```

Run quality checks before submitting changes:

```bash
uv run ruff format .        # mise run format
uv run ruff check --fix .   # mise run format
uv run mypy packages/core   # mise run mypy
uv run pytest               # mise run test, mise run test-unit, mise run test-integration
```

The project includes mise configuration for automatic tool management. Use
`mise install` followed by `mise run install` to set up the environment. See
[mise.toml](mise.toml) or run `mise tasks` for details.

See [.github/CONTRIBUTING.md](.github/CONTRIBUTING.md) for plugin development
guidelines.

## Project history

Originally created by [@Ximaz](https://github.com/Ximaz) before 2023. The
repository was later deleted or made private. Current maintainer
[@totallynotdavid](https://github.com/totallynotdavid) rebuilt the codebase from
scratch to fix platform changes and modernize the architecture.

Feature discussions and issue reports take place on
[GitHub Discussions](https://github.com/totallynotdavid/megaloader/discussions).
