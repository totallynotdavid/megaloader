# Contributing to Megaloader

Thank you for considering contributing to Megaloader! This guide will help you
get started.

## Getting Started

### Prerequisites

- Python 3.10 or higher (3.13+ recommended)
- [uv](https://docs.astral.sh/uv/) package manager
- [mise](https://mise.jdx.dev/) (optional but recommended)
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
mise install
mise run install

# Or using uv directly
uv sync --all-groups
```

3. Install packages in editable mode:

```bash
uv pip install -e packages/megaloader
uv pip install -e packages/cli
```

4. Run tests to verify setup:

```bash
mise test-unit
```

## Development Workflow

### Code Style

We use Ruff for formatting and linting:

```bash
# Format and lint
mise run format

# Or manually
ruff format .
ruff check --fix .
```

### Type Checking

We maintain strict type checking with mypy:

```bash
mise run mypy
```

All code must pass type checking before submission.

### Testing

Run the test suite:

```bash
# Unit tests only (no network)
mise test-unit

# All tests including integration
mise test

# Specific test file
uv run pytest packages/megaloader/tests/unit/test_http.py -v
```

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
megaloader/
├── packages/
│   ├── megaloader/          # Core library
│   │   ├── megaloader/      # Source code
│   │   │   ├── __init__.py
│   │   │   ├── plugin.py
│   │   │   ├── http.py
│   │   │   └── plugins/
│   │   └── tests/
│   └── cli/                 # CLI tool
├── docs/                    # Documentation
└── demo/                    # Django demo
```

## Areas for Contribution

### High Priority

- **Bug Fixes**: Fix issues with existing plugins
- **Test Coverage**: Add more unit and integration tests
- **Documentation**: Improve guides and API docs

### Medium Priority

- **New Core Plugins**: Well-maintained platforms with stable APIs
- **CLI Enhancements**: New commands or options
- **Performance**: Optimize download speeds

### Low Priority

- **Extended Plugins**: Additional platforms (may break)
- **UI**: Improvements to demo website

## Adding Features

### New Core Plugin

See [Creating Plugins](creating-plugins.md) for detailed guide.

### New CLI Command

1. Add command in `packages/cli/megaloader_cli/main.py`
2. Update CLI documentation
3. Add tests

### New Feature

1. Discuss in GitHub Issues first
2. Create implementation plan
3. Write tests first (TDD)
4. Implement feature
5. Update documentation

## Code Review

### What We Look For

- **Correctness**: Does it work as intended?
- **Tests**: Are there tests covering the changes?
- **Style**: Does it follow project conventions?
- **Performance**: Is it reasonably efficient?
- **Documentation**: Are changes documented?

### Review Process

1. Automated checks run on PR
2. Maintainer reviews code
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
