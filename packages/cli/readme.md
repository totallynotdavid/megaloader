# [pkg]: megaloader-cli

[![PyPI version](https://badge.fury.io/py/megaloader-cli.svg)](https://badge.fury.io/py/megaloader-cli)

Command-line interface for the megaloader library. Extract metadata and download
files from supported hosting platforms directly in your terminal.

## Installation

```bash
pip install megaloader-cli
```

The CLI installs the core megaloader library as a dependency. Both packages can
be used independently.

## Basic usage

List available files without downloading:

```bash
megaloader extract https://pixeldrain.com/l/abc123
```

Download files to a directory:

```bash
megaloader download https://pixeldrain.com/l/abc123 ./downloads
```

List supported platforms:

```bash
megaloader plugins
```

## Commands

The `extract` command shows file metadata without downloading anything. Add
`--json` for machine-readable output or `--verbose` for debug logs:

```bash
megaloader extract https://pixeldrain.com/l/abc123
megaloader extract https://gofile.io/d/xyz456 --json
megaloader extract https://cyberdrop.me/a/album --verbose
```

The `download` command saves files to the specified directory. Defaults to
`./downloads` when omitted. Files are grouped into collection subfolders by
default:

```bash
megaloader download https://pixeldrain.com/l/abc123
megaloader download https://cyberdrop.me/a/album ./my-files
megaloader download https://bunkr.si/a/xyz789 ./downloads --verbose
```

Add `--flat` to disable subfolders and write all files directly to the output
directory. Use `--filter` to download only files matching a glob pattern:

```bash
megaloader download https://pixeldrain.com/l/abc123 ./downloads --flat
megaloader download https://cyberdrop.me/a/album ./videos --filter "*.mp4"
megaloader download https://bunkr.si/a/xyz789 ./images --filter "*.{jpg,png}"
```

GoFile password-protected content requires the `--password` argument:

```bash
megaloader download https://gofile.io/d/protected ./downloads --password secret123
```

The `plugins` command lists all supported platforms and domains.

## Common patterns

Preview files before downloading:

```bash
megaloader extract https://pixeldrain.com/l/abc123
megaloader download https://pixeldrain.com/l/abc123 ./downloads
```

Filter by type to download only what you need:

```bash
megaloader download https://cyberdrop.me/a/album ./videos --filter "*.mp4"
megaloader download https://bunkr.si/a/xyz ./images --filter "*.jpg"
```

Control file organization with the `--flat` flag:

```bash
megaloader download https://pixeldrain.com/l/abc ./organized
megaloader download https://pixeldrain.com/l/abc ./flat --flat
```

Enable verbose logging for troubleshooting:

```bash
megaloader download https://example.com/file ./downloads --verbose
```

## Relationship to core library

The CLI wraps the core megaloader library. It handles argument parsing, output
formatting, and file downloads. The core library performs URL detection,
metadata extraction, and platform-specific logic.

Use the CLI for terminal workflows, quick downloads, and platform exploration.
Use the core library for Python integration, custom handling, progress tracking,
and batch processing. See the core library documentation for programmatic usage.

## Development

The CLI is part of a uv workspace. Install from the repository root:

```bash
uv sync
uv run megaloader --help
```

Install in editable mode for development:

```bash
uv pip install -e packages/cli
```

Run `uv run ruff format .` and the test suite before committing.

## Contributing

Contributions are welcome. See the repository contributing guide for setup and
submission details. Report bugs and request features through GitHub Discussions.
Include your Python version, error messages, and problematic URLs.
