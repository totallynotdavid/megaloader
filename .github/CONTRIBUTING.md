# Contributing

[`architecture.md`](../architecture.md) maps the code. The
[manual](https://totallynotdavid.github.io/megaloader) documents the library and
the CLI.

## Set up

The repository pins its tools in `mise.toml`: Python, uv, ruff, bun, and biome.

```bash
git clone https://github.com/totallynotdavid/megaloader
cd megaloader
mise install
mise run sync
```

Without mise, install Python 3.10 or newer and uv, then:

```bash
uv sync --all-packages --extra dev
cd apps/api && uv sync --extra dev
```

## Check your change

```bash
mise run check
mise run test
```

`check` runs these tasks:

| Task                         | Does                                      |
| ---------------------------- | ----------------------------------------- |
| `mise run format`            | `ruff format` and `ruff check --fix`      |
| `mise run lint`              | `mypy` on the workspace and on `apps/api` |
| `mise run test-unit`         | Core unit tests and the script tests      |
| `mise run test-api`          | The API tests                             |
| `mise run validate-snippets` | Checks Python blocks in `apps/docs` parse |

`mise run test` adds the offline plugin tests, which replay recorded responses
with the network blocked. `mise run dev-cli -- extract <url>` runs the CLI from
the working tree.

## Commit and open a pull request

Branch from `main`. Keep each pull request focused on one change. Write each
commit subject as `area: imperative lowercase summary`, as in
`api: replace httpx with httpx2`. Describe the problem and the fix in the pull
request, and update the docs when behavior changes.

## Add a platform

[Writing plugins](https://totallynotdavid.github.io/megaloader/writing-plugins)
walks through a plugin end to end, and
[Testing plugins](https://totallynotdavid.github.io/megaloader/testing-plugins)
covers its tests. A new plugin needs:

- `packages/core/megaloader/plugins/<name>.py`
- Entries in `PLUGIN_REGISTRY` and `PLUGIN_NAME_REGISTRY`
- Fixture URLs in `packages/core/tests/test_urls.py`
- A recorded test, and unit tests for URL handling and failures
- Rows in `apps/docs/megaloader/platforms.md` and, for options, in
  `plugin-options.md`

Recording needs the proxy credentials listed in Testing plugins.

## Change the docs

The manual is a VitePress site in `apps/docs/megaloader/`:

```bash
mise run docs-serve        # http://localhost:5173
mise run docs-build        # exits 1 on a dead link
mise run format-docs       # biome for Vue, prettier for Markdown
mise run validate-snippets
```

Markdown wraps at 80 columns:

```bash
bunx prettier --print-width 80 --prose-wrap always --write '**/*.md'
```

## Update tool versions

`scripts/update-tool-versions.py` changes one tool's version in every file that
pins it:

```bash
python scripts/update-tool-versions.py --tool ruff --version 0.15.0 --dry-run
```

See [`scripts/readme.md`](../scripts/readme.md) for the tools it supports.

## Release

A release is a tag. The tag version must equal the `version` in the package's
`pyproject.toml`, or the workflow stops.

| Tag           | Workflow           | Publishes                                                                                                   |
| ------------- | ------------------ | ----------------------------------------------------------------------------------------------------------- |
| `vcore-X.Y.Z` | `release-core.yml` | `megaloader` on PyPI                                                                                        |
| `vcli-X.Y.Z`  | `release-cli.yml`  | `megaloader-cli` on PyPI, and a GitHub release with `megaloader-cli-linux` and `megaloader-cli-windows.exe` |

Before tagging, set the new version in `packages/<core|cli>/pyproject.toml` and
in the package's `__version__` (`megaloader/_version.py` for core,
`megaloader_cli/__init__.py` for the CLI). PyPI publishing uses a trusted
publisher in the `pypi` GitHub environment. `mise run build-bin` builds the
Windows binary locally to test the PyInstaller build.

## Get help

Ask questions and float ideas in
[GitHub Discussions](https://github.com/totallynotdavid/megaloader/discussions).
Report a bug through the issue templates, with your Python version, the full
error message, and the URL.
