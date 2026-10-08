# Contributing

Megaloader contains a Python library, a CLI, an HTTP API, and a VitePress
manual. The [architecture map](../docs/architecture.md) shows their boundaries;
the [manual](https://totallynotdavid.github.io/megaloader) describes the
user-facing behavior.

## Set up

The repository pins Python, uv, ruff, bun, and biome in `mise.toml`.

```bash
git clone https://github.com/totallynotdavid/megaloader
cd megaloader
mise install
mise run sync
```

Without mise, install Python 3.10 or newer and uv:

```bash
uv sync --all-packages --extra dev
cd apps/api && uv sync --extra dev
```

## Check a change

Run the quick checks and the offline suite:

```bash
mise run check
mise run test
```

`check` formats Python, runs type checks, runs unit and API tests, and parses
Python snippets in `apps/docs`. `test` replays the plugin recordings with the
network blocked. To run the CLI from the working tree:

```bash
mise run dev-cli -- extract <url>
```

## Add a platform

Follow
[Writing plugins](https://totallynotdavid.github.io/megaloader/writing-plugins)
and
[Testing plugins](https://totallynotdavid.github.io/megaloader/testing-plugins).
A platform change includes the plugin, both registry entries, fixture URLs, a
recorded plugin test, unit tests for URL handling and failures, and the platform
table. Add an entry to `apps/docs/megaloader/plugin-options.md` when the plugin
accepts options.

## Change the manual

The manual is in `apps/docs/megaloader/`:

```bash
mise run docs-serve
mise run docs-build
mise run format-docs
mise run validate-snippets
```

`docs-build` fails when VitePress finds a dead link. `format-docs` formats Vue
files with Biome and Markdown with Prettier. Markdown uses an 80-column prose
width:

```bash
bunx prettier --print-width 80 --prose-wrap always --write '**/*.md'
```

## Submit a change

Branch from `main` and keep a pull request focused. Write the commit subject as
`area: imperative lowercase summary`. Describe the problem and the fix, and
update the manual when behavior changes. Report bugs with the Python version,
the complete error, and the source URL.

## Update tool versions

[`scripts/update-tool-versions.py`](../scripts/update-tool-versions.py) changes
one tool's version in every file that pins it:

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
