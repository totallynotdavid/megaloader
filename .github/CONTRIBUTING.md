# Contributing

Megaloader contains a Python library, a CLI, an HTTP API, and a VitePress
manual. The [architecture map](../docs/architecture.md) shows their boundaries;
the [manual](https://totallynotdavid.github.io/megaloader) describes the
user-facing behavior.

## Set up

The repository pins Python, uv, ruff, and Bun in `mise.toml`. The docs lockfile
pins the JavaScript tooling.

```bash
git clone https://github.com/totallynotdavid/megaloader
cd megaloader
mise run install
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

`check` is read-only. It checks formatting, runs strict type checks, runs the
offline core and API tests, builds the packages and manual, and parses Python
snippets in `apps/docs`. `test` replays the plugin recordings with the network
blocked. To run the CLI from the working tree:

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
mise run build:docs
mise run fix
mise run validate-snippets
```

`build:docs` fails when VitePress finds a dead link. `fix` formats Vue files and
Markdown with oxfmt. Markdown uses an 80-column prose width.

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

Before tagging, set the new version in `packages/<core|cli>/pyproject.toml`. For
core, also set `__version__` in `packages/core/megaloader/_version.py`. Write
the announcement to `.github/release-notes-core.md` or
`.github/release-notes-cli.md`. Its first line must be
`megaloader X.Y.Z is out.` for core or `megaloader-cli X.Y.Z is out.` for the
CLI. Each workflow stops before it builds when the tag, the manifests or that
first line disagree. The CLI release body is that file followed by GitHub's
generated change list. The CLI requires the matching core release, so tag
`vcore-*` first when both change. PyPI publishing uses a trusted publisher in
the `pypi` GitHub environment. `mise run build-bin` builds the Windows binary
locally to test the PyInstaller build.
