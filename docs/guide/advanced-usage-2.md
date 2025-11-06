# Setup Guide for Megaloader Monorepo

## Quick Start

1. **Clone and setup:**
   ```bash
   git clone https://github.com/totallynotdavid/megaloader
   cd megaloader
   git checkout monorepo  # If working from this branch
   ```

2. **Install dependencies:**
   ```bash
   # Using mise (recommended)
   mise install
   mise run install

   # Or using uv directly
   uv sync --all-groups
   ```

3. **Install packages:**
   ```bash
   # Core library
   uv pip install -e packages/megaloader

   # CLI tool (optional)
   uv pip install -e packages/cli

   # Demo website (optional)
   cd demo
   uv pip install -e .
   python manage.py migrate
   cd ..
   ```

4. **Verify installation:**
   ```bash
   # Test core library
   python -c "import megaloader; print('Success!')"

   # Test CLI
   .\.venv\Scripts\megaloader.exe list-plugins

   # Run tests
   uv run pytest packages/megaloader/tests/unit -v
   ```

## Development Tasks

```bash
# Format and lint
mise run format

# Type checking
mise run mypy

# Run all tests
mise run test

# Run unit tests only
mise run test-unit

# Serve documentation
mise run docs-serve

# Run demo website
mise run demo-run
```

## Package Structure

```
megaloader/
├── packages/
│   ├── megaloader/         # Core library
│   │   ├── megaloader/     # Package source
│   │   ├── tests/          # Test suite
│   │   └── pyproject.toml
│   └── cli/                # CLI tool
│       ├── megaloader_cli/
│       └── pyproject.toml
├── docs/                   # Documentation
│   ├── mkdocs.yml
│   └── docs/
├── demo/                   # Django demo
│   ├── config/
│   ├── downloader/
│   └── pyproject.toml
└── pyproject.toml          # Workspace config
```

## Troubleshooting

### "Module not found" errors
Make sure packages are installed in editable mode:
```bash
uv pip install -e packages/megaloader
uv pip install -e packages/cli
```

### CLI command not found
Use the full path or activate the venv:
```bash
.\.venv\Scripts\megaloader.exe --version
```

### Tests not found
Verify pytest.ini has correct testpaths:
```ini
testpaths = packages/megaloader/tests
```
