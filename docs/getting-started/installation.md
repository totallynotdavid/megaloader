# Installation

## Requirements

- Python 3.10 or higher
- pip or uv package manager (uv recommended)

## Core Library

Install the core library for programmatic usage:

```bash
pip install megaloader
```

Or using uv (recommended):

```bash
uv pip install megaloader
```

This installs the `megaloader` package, which provides the `extract()` function and related APIs for metadata extraction.

## CLI Tool

The command-line interface is distributed as a separate package. Install it if you want to use Megaloader from the terminal:

```bash
pip install megaloader-cli
```

Or using uv:

```bash
uv pip install megaloader-cli
```

The CLI package automatically installs the core library as a dependency.

## Install from Source

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

## Development Installation

For contributors working on Megaloader itself:

```bash
# Install all workspace dependencies including dev tools
uv sync --all-groups

# Or install individual packages with dev dependencies
uv pip install -e "packages/core[dev]"
uv pip install -e "packages/cli[dev]"
```

This installs additional tools like pytest, ruff, and mypy for testing and code quality.

## Verify Installation

### Core Library

Verify the core library installation:

```python
import megaloader as mgl

# Check version
print(mgl.__version__)

# Try extracting from a URL
for item in mgl.extract("https://pixeldrain.com/u/example"):
    print(f"Found: {item.filename}")
```

### CLI Tool

Verify the CLI installation:

```bash
megaloader --version
```

List supported platforms:

```bash
megaloader plugins
```

## Next Steps

- [Quick Start Guide](quickstart.md) - Get started in 5 minutes
- [Core Library Overview](../core/overview.md) - Learn about the extraction API
- [CLI Commands](../cli/commands.md) - Command-line reference
