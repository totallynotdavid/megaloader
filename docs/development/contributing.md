# Contributing to Megaloader

Thank you for considering contributing to Megaloader! This guide will help you
get started with development, testing, and documentation contributions.

## Getting Started

### Prerequisites

- Python 3.10 or higher (3.13+ recommended for reproducibility)
- [uv](https://docs.astral.sh/uv/) package manager (v0.9.10+)
- [mise](https://mise.jdx.dev/) (optional but recommended for task management)
- Git

### Development Setup

1. Fork and clone the repository:

```bash
git clone https://github.com/YOUR_USERNAME/megaloader.git
cd megaloader
```

2. Install dependencies:

```bash
# Using mise (recommended)
mise install              # Install Python, uv, ruff, and other tools
mise run sync             # Install workspace dependencies

# Or using uv directly
uv sync --all-packages --extra dev
```

3. Verify installation:

```bash
# Run unit tests to verify setup
mise run test-unit

# Or using uv directly
uv run pytest packages/core/tests/unit
```

The workspace uses uv's workspace feature, so all packages are automatically
installed in editable mode.

## Development Workflow

### Code Style

We use **ruff** (v0.14.5) for both formatting and linting, replacing black,
isort, and flake8:

```bash
# Format and fix linting issues
mise run format

# Or manually
ruff format .
ruff check --fix .
```

**Style Guidelines:**

- Line length: 88 characters (ruff default)
- Target version: Python 3.10
- Import style: Absolute imports preferred, relative imports banned
- Type hints: Required for core library

### Type Checking

We maintain strict type checking with **mypy**:

```bash
# Run type checking
mise run lint

# Or manually
uv run mypy packages/core/megaloader
```

All code in the core library must pass strict type checking before submission.

### Testing

We use **pytest** with two types of tests:

```bash
# Unit tests only (fast: <1 sec, no network)
mise run test-unit

# All tests including live network tests (~100 secs)
mise run test

# Specific test file
uv run pytest packages/core/tests/unit/test_item.py -v

# Run with verbose output
uv run pytest packages/core/tests -v
```

**Test Organization:**

- `tests/unit/` - Unit tests with no network access (fast)
- `tests/live/` - Live network tests marked with `@pytest.mark.live`
- `tests/conftest.py` - Pytest fixtures and configuration
- `tests/helpers.py` - Shared test utilities

**Writing Tests:**

- Use `@pytest.mark.live` for tests requiring network access
- Unit tests should be fast and not depend on external services
- Follow existing test patterns in the codebase

### Commit Messages

Follow conventional commits:

```
feat: add support for new platform
fix: correct URL parsing for Bunkr
docs: update installation instructions
test: add tests for Cyberdrop plugin
refactor: simplify HTTP retry logic
```

## Contributing Code

### Pull Request Process

1. Create a feature branch:

```bash
git checkout -b feature/your-feature-name
```

2. Make your changes and commit:

```bash
git add .
git commit -m "feat: description of your changes"
```

3. Push to your fork:

```bash
git push origin feature/your-feature-name
```

4. Create a Pull Request on GitHub

### PR Requirements

- [ ] Code passes all tests
- [ ] Code is formatted with Ruff
- [ ] Type hints are added/updated
- [ ] Documentation is updated
- [ ] Tests are added for new features
- [ ] Commit messages follow conventions

## Project Structure

```
megaloader/                    # Root workspace
├── packages/
│   ├── core/                  # Core library (megaloader on PyPI)
│   │   ├── megaloader/        # Main package
│   │   │   ├── plugins/       # Platform-specific extractors
│   │   │   ├── plugin.py      # BasePlugin abstract class
│   │   │   ├── item.py        # DownloadItem dataclass
│   │   │   ├── exceptions.py  # Custom exceptions
│   │   │   └── __init__.py    # Public API exports
│   │   ├── tests/             # Test suite
│   │   │   ├── unit/          # Unit tests
│   │   │   ├── live/          # Live network tests
│   │   │   ├── conftest.py    # Pytest fixtures
│   │   │   └── helpers.py     # Test utilities
│   │   └── pyproject.toml     # Package configuration
│   │
│   └── cli/                   # CLI tool (megaloader-cli on PyPI)
│       ├── megaloader_cli/    # CLI package
│       │   ├── main.py        # Click CLI entry point
│       │   └── ...
│       └── pyproject.toml     # Package configuration
│
├── api/                       # FastAPI demo server
│   ├── main.py                # FastAPI application
│   └── pyproject.toml         # Package configuration
│
├── docs/                      # VitePress documentation
│   ├── getting-started/       # Installation & quickstart
│   ├── core/                  # Core library docs
│   ├── cli/                   # CLI documentation
│   ├── plugins/               # Plugin documentation
│   └── development/           # Contributing guides
│
├── pyproject.toml             # Workspace configuration
├── uv.lock                    # Dependency lock file
└── mise.toml                  # Development tasks
```

## Areas for Contribution

### High Priority

- **Bug Fixes**: Fix issues with existing plugins
- **Test Coverage**: Add more unit and live tests
- **Documentation**: Improve guides, API docs, and examples
- **Core Plugins**: Maintain and improve Bunkr, PixelDrain, Cyberdrop, GoFile

### Medium Priority

- **New Core Plugins**: Well-maintained platforms with stable APIs
- **CLI Enhancements**: New commands or options
- **Performance**: Optimize extraction speed and memory usage

### Low Priority

- **Extended Plugins**: Additional platforms (best-effort support)
- **API Demo**: Improvements to FastAPI demo server

## Adding Features

### New Core Plugin

See [Creating Plugins](../plugins/creating-plugins.md) for a detailed guide on
implementing platform extractors.

**Quick checklist:**

1. Create new plugin file in `packages/core/megaloader/plugins/`
2. Inherit from `BasePlugin` and implement `extract()` method
3. Register plugin in `PLUGIN_REGISTRY`
4. Add unit tests in `tests/unit/`
5. Add live tests in `tests/live/` with `@pytest.mark.live`
6. Update documentation in `docs/plugins/supported-platforms.md`

### New CLI Command

1. Add command in `packages/cli/megaloader_cli/main.py` using Click decorators
2. Update `docs/cli/commands.md` with command documentation
3. Add examples to `docs/cli/examples.md`
4. Test command manually

### New Core Library Feature

1. Discuss in GitHub Issues first
2. Create implementation plan
3. Write tests first (TDD approach)
4. Implement feature in `packages/core/megaloader/`
5. Update API reference in `docs/core/api-reference.md`
6. Add usage examples to relevant documentation pages

## Contributing to Documentation

We use **VitePress** for documentation. Contributions to improve clarity,
accuracy, and completeness are highly valued.

### Documentation Setup

1. Install Node.js dependencies:

```bash
cd docs
bun install
```

2. Run local development server:

```bash
# Using mise
mise run docs-serve

# Or manually
cd docs
bun run docs:dev
```

3. Build documentation:

```bash
# Using mise
mise run docs-build

# Or manually
cd docs
bun run docs:build
```

### Documentation Guidelines

**Structure:**

- Use consistent file naming: `kebab-case.md`
- Organize content in logical directories
- Separate conceptual guides from reference material
- Progress from simple to advanced topics

**Code Examples:**

- Use `extract()` function, not deprecated `download()`
- Show `DownloadItem` objects with correct field names
- Use `import megaloader as mgl` for imports
- Include complete, runnable examples
- Add syntax highlighting with ` ```python `

**Style:**

- Use clear, concise language
- Define technical terms before using them
- Include practical examples for each concept
- Use relative links for internal navigation
- Keep line length reasonable for readability

**What to Document:**

- New features and API changes
- Plugin-specific options and requirements
- Common usage patterns and workflows
- Error handling and troubleshooting
- Breaking changes and migration guides

### Updating Documentation

When making code changes, update relevant documentation:

1. **API Changes**: Update `docs/core/api-reference.md`
2. **New Plugin**: Update `docs/plugins/supported-platforms.md`
3. **CLI Changes**: Update `docs/cli/commands.md`
4. **New Feature**: Add examples to appropriate guide pages

## Code Review

### What We Look For

- **Correctness**: Does it work as intended?
- **Tests**: Are there tests covering the changes?
- **Style**: Does it follow project conventions?
- **Performance**: Is it reasonably efficient?
- **Documentation**: Are changes documented?
- **Type Safety**: Are type hints correct and complete?

### Review Process

1. Automated checks run on PR (ruff, mypy, pytest)
2. Maintainer reviews code and documentation
3. Discussion and iteration
4. Approval and merge

## Getting Help

- **Questions**: Use
  [GitHub Discussions](https://github.com/totallynotdavid/megaloader/discussions)
- **Bugs**: Open an
  [Issue](https://github.com/totallynotdavid/megaloader/issues)
- **Slack/Discord**: Coming soon

## License

By contributing, you agree that your contributions will be licensed under the
MIT License.

## Recognition

Contributors are recognized in:

- README.md
- Release notes
- GitHub contributors page

Thank you for contributing! 🎉
