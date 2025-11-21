# CLI Overview

The Megaloader CLI provides a command-line interface for extracting metadata and downloading files from supported platforms. It's a thin wrapper around the core library that adds terminal-friendly output, progress tracking, and convenient command-line options.

## Purpose

The CLI tool is designed for:

- **Quick metadata extraction** without writing code
- **One-off downloads** from the terminal
- **Shell scripting** and automation workflows
- **Exploring platform content** before implementing custom logic
- **Testing and debugging** extraction behavior

## Installation

The CLI is distributed as a separate package from the core library.

### Using pip

```bash
pip install megaloader-cli
```

### Using uv

```bash
uv pip install megaloader-cli
```

### Verify Installation

After installation, verify the CLI is available:

```bash
megaloader --version
```

You should see output like:

```
megaloader, version 0.1.0
```

## Basic Command Structure

The CLI provides three main commands:

```bash
megaloader extract <URL>           # Extract metadata (dry run)
megaloader download <URL> [DIR]    # Download files
megaloader plugins                 # List supported platforms
```

All commands support the `--help` flag for detailed usage information:

```bash
megaloader --help
megaloader extract --help
megaloader download --help
```

## Common Options

Several options are available across commands:

- **`-v, --verbose`**: Enable debug logging to see detailed extraction process
- **`--json`**: Output structured JSON instead of human-readable text (extract only)
- **`--flat`**: Disable collection subfolder organization (download only)
- **`--filter`**: Filter files by glob pattern (download only)
- **`--password`**: Provide password for protected content (download only)

## When to Use CLI vs Library

### Use the CLI when:

- You need a quick one-time download
- You're exploring what content is available on a URL
- You're writing shell scripts or automation
- You want to pipe metadata to other tools (using `--json`)
- You don't need custom download logic

### Use the library when:

- You need custom download implementation (resume, retry, rate limiting)
- You're integrating extraction into a larger application
- You need fine-grained control over the extraction process
- You want to process items as they're discovered (streaming)
- You need to handle errors programmatically

## Quick Example

Extract metadata from a URL:

```bash
megaloader extract https://pixeldrain.com/l/abc123
```

Download files to a directory:

```bash
megaloader download https://pixeldrain.com/l/abc123 ./downloads
```

List all supported platforms:

```bash
megaloader plugins
```

## Next Steps

- See [Commands](/cli/commands) for detailed command reference
- See [Examples](/cli/examples) for common usage patterns
- See [Core Library](/core/overview) to use Megaloader programmatically
