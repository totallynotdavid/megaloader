# Contributing

Thank you for considering contributing to Megaloader. This guide covers
development setup, workflow, and contribution guidelines.

## Getting started

### Prerequisites

- Python 3.10+ (3.13+ recommended)
- [uv](https://docs.astral.sh/uv/) package manager (v0.9.10+)
- [mise](https://mise.jdx.dev/) (optional, for task management)
- Git

### Development setup

Fork and clone:

```bash
git clone https://github.com/YOUR_USERNAME/megaloader.git
cd megaloader
```

Install dependencies:

::: code-group

```bash [mise]
mise install
mise run sync
```

```bash [uv]
uv sync --all-packages --extra dev
```

:::

Verify:

::: code-group

```bash [mise]
mise run test-unit
```

```bash [uv]
uv run pytest packages/core/tests/unit
```

:::

The workspace uses uv's workspace feature, so all packages are installed in
editable mode.

## Development workflow

### Code style

We use ruff (v0.14.5) for formatting and linting:

::: code-group

```bash [mise]
mise run format
```

```bash [manual]
ruff format .
ruff check --fix .
```

:::

**Style guidelines:** Line length 88 characters, target Python 3.10, absolute
imports preferred, type hints required for core library.

### Type checking

We maintain strict type checking with mypy:

::: code-group

```bash [mise]
mise run lint
```

```bash [manual]
uv run mypy packages/core/megaloader
```

:::

All core library code must pass strict type checking.

### Testing

```bash
mise run test-unit

mise run test

uv run pytest packages/core/tests/unit/test_item.py -v

uv run pytest packages/core/tests -v
```

**Test organization:**

- `tests/unit/` - Unit tests with no network access (fast)
- `tests/live/` - Live network tests marked with `@pytest.mark.live`
- `tests/conftest.py` - Pytest fixtures and configuration
- `tests/helpers.py` - Shared test utilities

**Writing tests:** Use `@pytest.mark.live` for tests requiring network access.
Unit tests should be fast and not depend on external services.

### Commit messages

Follow conventional commits:

```
feat: add support for new platform
fix: correct URL parsing for Bunkr
docs: update installation instructions
test: add tests for Cyberdrop plugin
refactor: simplify HTTP retry logic
```

## Contributing code

### Pull request process

Create feature branch:

```bash
git checkout -b feature/your-feature-name
```

Make changes and commit:

```bash
git add .
git commit -m "feat: description of your changes"
```

Push to fork:

```bash
git push origin feature/your-feature-name
```

Create Pull Request on GitHub.

### PR requirements

- Code passes all tests
- Code is formatted with Ruff
- Type hints are added/updated
- Documentation is updated
- Tests are added for new features
- Commit messages follow conventions

## Project structure

```
megaloader/
├── packages/
│   ├── core/
│   │   ├── megaloader/
│   │   │   ├── plugins/
│   │   │   ├── plugin.py
│   │   │   ├── item.py
│   │   │   ├── exceptions.py
│   │   │   └── __init__.py
│   │   ├── tests/
│   │   │   ├── unit/
│   │   │   ├── live/
│   │   │   ├── conftest.py
│   │   │   └── helpers.py
│   │   └── pyproject.toml
│   │
│   └── cli/
│       ├── megaloader_cli/
│       │   └── main.py
│       └── pyproject.toml
│
├── docs/
│   ├── guide/
│   ├── reference/
│   └── development/
│
├── pyproject.toml
├── uv.lock
└── mise.toml
```

## Areas for contribution

### High priority

- Bug fixes for existing plugins
- Test coverage improvements
- Documentation enhancements
- Core plugin maintenance (Bunkr, PixelDrain, Cyberdrop, GoFile)

### Medium priority

- New core plugins with stable APIs
- CLI enhancements
- Performance optimizations

### Low priority

- Extended plugins (additional platforms)
- API demo improvements

## Adding features

### New core plugin

See the creating plugins guide for details.

**Quick checklist:**

1. Create plugin file in `packages/core/megaloader/plugins/`
2. Inherit from `BasePlugin` and implement `extract()`
3. Register in `PLUGIN_REGISTRY`
4. Add unit tests in `tests/unit/`
5. Add live tests in `tests/live/` with `@pytest.mark.live`
6. Update `docs/reference/platforms.md`

### New CLI command

1. Add command in `packages/cli/megaloader_cli/main.py` using Click
2. Update `docs/reference/cli.md`
3. Add examples to `docs/guide/cli.md`
4. Test manually

### New core library feature

1. Discuss in GitHub Issues first
2. Create implementation plan
3. Write tests first (TDD approach)
4. Implement in `packages/core/megaloader/`
5. Update `docs/reference/api.md`
6. Add usage examples

## Contributing to documentation

We use VitePress for documentation. Contributions to improve clarity and
completeness are valued.

### Documentation setup

Install dependencies:

```bash
cd docs
bun install
```

Run development server:

::: code-group

```bash [mise]
mise run docs-serve
```

```bash [manual]
cd docs
bun run docs:dev
```

:::

Build:

::: code-group

```bash [mise]
mise run docs-build
```

```bash [manual]
cd docs
bun run docs:build
```

:::

### Documentation guidelines

**Structure:** Use kebab-case file naming, organize logically, separate guides
from reference, progress from simple to advanced.

**Code examples:** Use `extract()` function, show `DownloadItem` objects
correctly, use `import megaloader as mgl`, include complete runnable examples.

**Style:** Use clear concise language, define technical terms, include practical
examples, use relative links, keep lines readable.

### Updating documentation

When making code changes, update relevant documentation:

1. API changes → `docs/reference/api.md`
2. New plugin → `docs/reference/platforms.md`
3. CLI changes → `docs/reference/cli.md`
4. New feature → Add to appropriate guide

## Code review

### What we look for

- Correctness
- Tests coverage
- Style consistency
- Performance
- Documentation
- Type safety

### Review process

1. Automated checks run on PR
2. Maintainer reviews code and documentation
3. Discussion and iteration
4. Approval and merge

## Getting help

- Questions:
  [GitHub Discussions](https://github.com/totallynotdavid/megaloader/discussions)
- Bugs: [Issues](https://github.com/totallynotdavid/megaloader/issues)

## License

By contributing, you agree that your contributions will be licensed under the
MIT License.

## Recognition

Contributors are recognized in README.md, release notes, and GitHub contributors
page.

Thank you for contributing!
