# Megaloader CLI

Command-line interface for the Megaloader library.

## Installation

From the workspace root:

```bash
uv pip install -e packages/cli
```

## Usage

Download a file:

```bash
megaloader download-url "https://pixeldrain.com/u/95u1wnsd" ./downloads
```

List available plugins:

```bash
megaloader list-plugins
```

Enable verbose output:

```bash
megaloader download-url "https://example.com/file" ./downloads --verbose
```

Use proxy:

```bash
megaloader download-url "https://example.com/file" ./downloads --use-proxy
```

## Development

Install in development mode:

```bash
cd packages/cli
uv pip install -e ".[dev]"
```
