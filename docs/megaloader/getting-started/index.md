---
title: Getting started
description: Quick guide to installing and using Megaloader to extract metadata from file hosting platforms in 5 minutes.
outline: [2, 3]
prev:
  text: 'Home'
  link: '/'
next:
  text: 'Installation'
  link: '/getting-started/installation'
---

# Getting started

Welcome to Megaloader! This guide will get you up and running in under 5 minutes.

## What you'll learn

In this section, you'll learn how to:

1. **Install** Megaloader (core library and CLI tool)
2. **Extract metadata** from your first URL
3. **Download files** using the extracted metadata
4. **Use the CLI** for quick downloads

::: tip ⏱️ Estimated time
**5-10 minutes** to complete both installation and quickstart
:::

## Prerequisites

Before you begin, make sure you have:

- **Python 3.10 or higher** installed
- Basic familiarity with Python (for library usage)
- Terminal/command-line access

::: details Check your Python version
```bash
python --version
# or
python3 --version
```

If you don't have Python installed, download it from [python.org](https://www.python.org/downloads/)
:::

## Learning path

1. Installation: Install Megaloader using pip or uv package manager. [See the installation guide](./installation).

2. Quick start: Learn the basics with simple examples. [Read the quick start guide](./quickstart).

3. Next steps: After completing the getting started guides:

- **For developers**: Continue to the [user guide](/guide/) to learn about the library API
- **For CLI users**: Jump to [CLI commands](/cli/commands) for command-line usage
- **For contributors**: See [creating plugins](/plugins/creating-plugins) to add platform support

## Two ways to use megaloader

Megaloader can be used as a **Python library** or a **CLI tool**:

::: code-group

```python [Library (Programmatic)]
import megaloader as mgl

# Extract metadata
for item in mgl.extract("https://pixeldrain.com/l/abc123"):
    print(f"Found: {item.filename}")
    # You implement download logic
```

```bash [CLI (Terminal)]
# Extract metadata
megaloader extract https://pixeldrain.com/l/abc123

# Download files
megaloader download https://pixeldrain.com/l/abc123 ./output
```

:::

Choose the library for custom integration and full control. Choose the CLI for quick one-off downloads and shell scripting.

## Need help?

- **Questions?** Check the [User Guide](/guide/)
- **CLI help?** See [CLI Commands](/cli/commands)
- **Found a bug?** [Open an issue](https://github.com/totallynotdavid/megaloader/issues)
- **Want to contribute?** Read the [contributing guide](/development/contributing)
