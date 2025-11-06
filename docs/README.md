# Megaloader Documentation

This directory contains the documentation website for Megaloader, built with MkDocs and the Material theme.

## Setup

Install documentation dependencies from the workspace root:

```bash
# From project root
uv sync --group docs
```

## Development

Serve the documentation locally with live reload:

```bash
cd docs
uv run mkdocs serve
```

Or using mise from the root directory:

```bash
mise run docs-serve
```

Then open http://localhost:8000 in your browser.

## Building

Build the static documentation site:

```bash
mkdocs build
```

The built site will be in the `site/` directory.

## Structure

```
docs/
├── mkdocs.yml           # MkDocs configuration
├── pyproject.toml       # Python dependencies
├── docs/                # Documentation content
│   ├── index.md
│   ├── getting-started/
│   ├── guide/
│   ├── api/
│   ├── cli/
│   └── development/
└── site/                # Built site (generated, gitignored)
```

## Deployment

The documentation can be deployed to GitHub Pages:

```bash
mkdocs gh-deploy
```

This builds the site and pushes it to the `gh-pages` branch.
