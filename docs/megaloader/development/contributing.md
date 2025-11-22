# Contributing

Thank you for considering contributing to Megaloader. This guide covers the
essentials for developers to get started and contribute effectively.

We review for correctness, test coverage, style, performance, documentation, and
type safety. Automated checks run on PRs, followed by maintainer review.

## Getting started

### Prerequisites

- Python 3.10+ (3.13+ recommended)
- [uv](https://docs.astral.sh/uv/) package manager (v0.9.10+)
- [mise](https://mise.jdx.dev/) (optional, for task management)
- Git

### Development setup

Fork and clone the repository:

```bash
git clone https://github.com/totallynotdavid/megaloader
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

Verify setup:

::: code-group

```bash [mise]
mise run test-unit
```

```bash [uv]
uv run pytest packages/core/tests/unit
```

:::

The workspace uses uv's workspace feature for editable installs.

## Development workflow

### Code style

We use Ruff for formatting and linting:

::: code-group

```bash [mise]
mise run format
```

```bash [manual]
ruff format .
ruff check --fix .
```

:::

**Guidelines:** 88-character lines, Python 3.10 target, absolute imports, type
hints required for core.

### Type checking

Strict mypy checking:

::: code-group

```bash [mise]
mise run lint
```

```bash [manual]
uv run mypy .
```

:::

### Testing

Run tests:

::: code-group

```bash [mise]
mise run test-unit  # Fast unit tests
mise run test       # All tests including live
```

```bash [uv]
uv run pytest packages/core/tests/unit/test_item.py -v
uv run pytest packages/core/tests -v
```

:::

**Organization:**

- `tests/unit/` - Fast unit tests (no network)
- `tests/live/` - Live tests with `@pytest.mark.live`
- Use `uv run pytest packages/core/tests --run-live` for live tests

### Commit messages

Follow conventional commits:

```
feat: add new platform support
fix: resolve Bunkr download issue
docs: update installation guide
test: add Cyberdrop plugin tests
refactor: simplify retry logic
```

## Contributing code

### Pull request process

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make changes and commit: `git commit -m "type: description"`
3. Push to your fork: `git push origin feature/your-feature`
4. Create a Pull Request on GitHub

**Requirements:**

- All tests pass
- Code formatted with Ruff
- Type hints updated
- Documentation updated
- New features have tests

See [GitHub's PR documentation](https://docs.github.com/en/pull-requests) for
details.

## Areas for contribution

### High priority

- Bug fixes for core plugins (Bunkr, PixelDrain, Cyberdrop, GoFile)
- Test coverage improvements
- Documentation updates

### Medium priority

- New core plugins with stable APIs
- CLI enhancements
- Performance optimizations

### Low priority

- Extended plugins for additional platforms
- API demo improvements

## Adding features

### New core plugin

See [creating plugins guide](../guide/creating-plugins).

**Checklist:**

1. Create plugin in `packages/core/megaloader/plugins/`
2. Inherit `BasePlugin`, implement `extract()`
3. Register in `PLUGIN_REGISTRY`
4. Add unit tests in `tests/unit/`
5. Add live tests with `@pytest.mark.live`
6. Update `docs/reference/platforms.md`

### New CLI command

1. Add to `packages/cli/megaloader_cli/main.py`
2. Update `docs/reference/cli.md` and `docs/guide/cli.md`

### New core feature

1. Discuss in
   [GitHub Discussions](https://github.com/totallynotdavid/megaloader/discussions)
2. Write tests first (TDD)
3. Implement in core library
4. Update `docs/reference/api.md`

## Contributing to documentation

We use VitePress. Setup:

```bash
cd docs
bun install
```

Run dev server:

::: code-group

```bash [mise]
mise run docs-serve
```

```bash [manual]
bun run docs:dev
```

:::

**Guidelines:** Clear language, complete examples, relative links. Update docs
with code changes.

## Getting help

For questions, ideas, or feedback, use
[GitHub Discussions](https://github.com/totallynotdavid/megaloader/discussions).
If you encounter a bug, please report it there first. Maintainers may convert it
to an Issue if necessary.
