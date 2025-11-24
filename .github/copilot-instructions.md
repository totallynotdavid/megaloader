# AI Coding Instructions for Megaloader

## Architecture Overview
Megaloader is a Python monorepo with three packages:
- **core** (`packages/core/`): Plugin-based library for extracting download metadata from file hosting platforms
- **cli** (`packages/cli/`): Command-line interface that wraps core and adds file downloading
- **api** (`apps/api/`): FastAPI server with rate limiting and size constraints

Core uses a plugin architecture where `extract(url)` detects the domain, selects a plugin from `PLUGIN_REGISTRY`, and yields `DownloadItem` objects lazily.

## Key Patterns
- **Plugins**: Inherit `BasePlugin`, implement `extract()` to yield `DownloadItem`. Override `_configure_session()` for authentication (e.g., cookies for Fanbox/Pixiv).
- **Error Handling**: Raise `ExtractionError` for network failures, `UnsupportedDomainError` for unknown domains.
- **CLI Commands**: Use `click` with Rich progress bars. Download organizes files into collection subfolders unless `--flat` is used.
- **API Endpoints**: Validate URLs against whitelist, check size limits (4MB default), return preview or download ZIP/single file.

## Development Workflow
- **Setup**: `uv sync --all-packages --extra dev` (or `mise run sync`)
- **Quality Checks**: `mise run format` (ruff format + fix), `mise run lint` (mypy), `mise run test-unit` (fast unit tests)
- **Full Tests**: `mise run test` (includes live network tests, ~100s)
- **Run CLI**: `uv run megaloader extract <url>` or `mise run dev-cli -- extract <url>`
- **Run API**: `cd apps/api; uv run uvicorn index:app --reload --host 0.0.0.0`
- **Build CLI Binary**: `mise run build-bin` (PyInstaller for Windows)
- **Docs**: `mise run docs-serve` (vitepress (Vue.js) site with bun), `mise run docs-build`, `mise run format-docs` (biome + prettier)

## CI/CD Workflows
- **Checks**: `.github/workflows/checks.yml` - runs format, lint, unit tests on push/PR
- **CodeQL**: `.github/workflows/codeql.yml` - security scanning
- **Coverage**: Codecov integration for test coverage reporting

## Conventions
- **Imports**: Absolute imports only, no relative (ruff ban-relative-imports)
- **Sessions**: Use `self.session` (lazy-loaded with retries) for HTTP requests
- **Testing**: Unit tests in `packages/core/tests/unit/`, live tests marked `@pytest.mark.live`
- **Linting**: Ruff with extensive rules (88 char lines, preview enabled)
- **Plugins**: Add to `PLUGIN_REGISTRY` in `plugins/__init__.py`, handle subdomains for Fanbox

## Examples
- **New Plugin**: See `plugins/pixeldrain.py` - parse HTML/JSON, yield `DownloadItem(download_url=..., filename=..., collection_name=...)`
- **CLI Download**: Filters with `fnmatch`, sanitizes filenames, uses Rich progress
- **API Response**: Returns `DownloadPreview` if size > limit, else streams ZIP

Reference: `packages/core/megaloader/`, `packages/cli/megaloader_cli/`, `apps/api/`, `mise.toml`, `apps/docs/`, `.github/workflows/`