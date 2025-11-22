---
title: Installation
description:
  Install megaloader core library and CLI tool using pip or uv package manager.
  Supports Python 3.10+.
outline: [2, 3]
prev:
  text: "Home"
  link: "/"
next:
  text: "Quick start"
  link: "/getting-started/quickstart"
---

# Installation

## Requirements

- Python 3.10 or higher
- pip or uv package manager (uv recommended)

## Core library

Install the core library for programmatic usage:

::: code-group

```bash [uv (recommended)]
uv pip install megaloader
```

```bash [pip]
pip install megaloader
```

:::

<!-- prettier-ignore -->
::: tip Why uv?
uv is significantly faster than pip and provides better dependency resolution.
[Learn more about uv](https://docs.astral.sh/uv/)
:::

This installs the `megaloader` package, which provides the `extract()` function
and related APIs for metadata extraction.

## CLI tool

The command-line interface is distributed as a separate package. Install it if
you want to use Megaloader from the terminal:

::: code-group

```bash [uv (recommended)]
uv pip install megaloader-cli
```

```bash [pip]
pip install megaloader-cli
```

:::

<!-- prettier-ignore -->
::: info Automatic dependencies
The CLI package automatically installs the core library as a dependency. You
don't need to install both.
:::

## Install from source

For development or to use the latest unreleased features:

```bash
# Clone the repository
git clone https://github.com/totallynotdavid/megaloader.git
cd megaloader

# Install core library
uv pip install -e packages/core

# Optionally install CLI
uv pip install -e packages/cli
```

## Development installation

For contributors working on Megaloader itself:

```bash
# Install all workspace dependencies including dev tools
uv sync --all-groups

# Or install individual packages with dev dependencies
uv pip install -e "packages/core[dev]"
uv pip install -e "packages/cli[dev]"
```

This installs additional tools like pytest, ruff, and mypy for testing and code
quality.

## Verify installation

### Core library

Verify the core library installation:

```python
import megaloader as mgl

# Check version
print(mgl.__version__)

# Try extracting from a URL
for item in mgl.extract("https://pixeldrain.com/u/example"):
    print(f"Found: {item.filename}")
```

### CLI tool

Verify the CLI installation:

```bash
megaloader --version
```

List supported platforms:

```bash
megaloader plugins
```
