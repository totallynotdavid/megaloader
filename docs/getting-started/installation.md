# Installation

## Requirements

- Python 3.10 or higher
- pip or uv package manager

## Install from PyPI

```bash
pip install megaloader
```

Or using uv:

```bash
uv pip install megaloader
```

## Install from Source

Clone the repository:

```bash
git clone https://github.com/totallynotdavid/megaloader.git
cd megaloader
```

Install the core library:

```bash
uv pip install -e packages/megaloader
```

## Install CLI

To use the command-line interface:

```bash
uv pip install -e packages/cli
```

## Development Installation

For development, install with all dependencies:

```bash
# Install workspace dependencies
uv sync --all-groups

# Or install individual packages
uv pip install -e "packages/megaloader[dev]"
uv pip install -e "packages/cli[dev]"
```

## Verify Installation

Verify the installation by importing the library:

```python
import megaloader
print(megaloader.__version__)
```

Or using the CLI:

```bash
megaloader --version
```

## Next Steps

- [Quick Start Guide](quickstart.md)
- [Basic Usage](../guide/basic-usage.md)
