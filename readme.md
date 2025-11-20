# [monorepo]: megaloader

[![CodeQL](https://github.com/totallynotdavid/megaloader/actions/workflows/codeql.yml/badge.svg)](https://github.com/totallynotdavid/megaloader/actions/workflows/codeql.yml)
[![lint and format check](https://github.com/totallynotdavid/megaloader/actions/workflows/checks.yml/badge.svg)](https://github.com/totallynotdavid/megaloader/actions/workflows/checks.yml)
[![codecov](https://codecov.io/gh/totallynotdavid/megaloader/graph/badge.svg?token=SBHAGJJB8L)](https://codecov.io/gh/totallynotdavid/megaloader)

Python library and CLI for extracting downloadable content from file hosting
platforms. Supports 11 platforms through a plugin architecture with automatic
URL detection.

## Installation

Install the core library for programmatic use:

```bash
pip install megaloader
```

Install the CLI tool for terminal usage:

```bash
pip install megaloader-cli
```

The packages are independent. Install both if you need library integration and
command-line access.

## Using the library

The library provides an `extract` function that detects the platform and
extracts file metadata:

```python
from megaloader import extract

for item in extract("https://pixeldrain.com/l/abc123"):
    print(f"{item.filename} - {item.download_url}")
```

Read the [core library documentation](packages/core/readme.md) for API details,
supported platforms, authentication, and download implementation.

## Using the CLI

The CLI extracts metadata and downloads files directly from the terminal:

```bash
megaloader download https://pixeldrain.com/l/abc123 ./downloads
```

Read the [CLI documentation](packages/cli/readme.md) for command reference and
usage patterns.

## Supported platforms

The library supports four core platforms with active maintenance and seven
extended platforms on best-effort basis. Core platforms receive priority for bug
fixes and feature development. Extended platforms work as of November 2025 but
may break without immediate fixes.

Core platforms are Bunkr, PixelDrain, Cyberdrop, and GoFile. Extended platforms
are Fanbox, Pixiv, Rule34, ThotsLife, ThotHub.VIP, ThotHub.TO, and Fapello.
Platform-specific features like authentication are documented in the core
library readme.

## Development

This monorepo uses uv workspaces. The core library lives in
`[packages/core/](packages/core/)` and the CLI in
`[packages/cli/](packages/cli/)`. Both are published independently to PyPI.
Development tools are configured at the root.

Clone and install dependencies:

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

The project includes mise configuration for automatic tool management. Run
`mise install` then `mise run install` to set up the environment. See
[mise.toml](mise.toml) for more details or run `mise tasks`.

See [.github/CONTRIBUTING.md](.github/CONTRIBUTING.md) for plugin development
guidelines.

## Project history

Originally created by [@Ximaz](https://github.com/Ximaz) before 2023. The
repository was later deleted or made private. Current maintainer
[@totallynotdavid](https://github.com/totallynotdavid) rebuilt the codebase from
scratch to fix platform changes and modernize the architecture.

Report issues and discuss features through
[GitHub Discussions](https://github.com/totallynotdavid/megaloader/discussions).
