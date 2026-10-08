# Architecture

Megaloader has a core library, a CLI, an HTTP API, and a manual. The CLI and the
API call the core library; the manual documents all three.

| Path            | Package          | Owns                                      |
| --------------- | ---------------- | ----------------------------------------- |
| `packages/core` | `megaloader`     | URL dispatch, plugins, items, and errors  |
| `packages/cli`  | `megaloader-cli` | The `megaloader` command and file writes  |
| `apps/api`      | `megaloader-api` | FastAPI validation, limits, and responses |
| `apps/docs`     | —                | The VitePress manual                      |

`packages/core` and `packages/cli` are members of the root uv workspace.
`apps/api` is a separate uv project with its own dependency installation. Its
`apps/api/pyproject.toml` takes `megaloader>=0.1.0` from PyPI, not from
`packages/core`, so Vercel's API deployment installs only the API project's
dependencies and does not see unbuilt core changes. `apps/docs` uses bun.

## Extraction path

`packages/core/megaloader/api.py` is the public entry point. `extract()`
validates the URL, resolves a plugin from the domain or the `plugin` argument,
constructs the fetcher, and yields the plugin's items as the caller iterates.

The core package contains these sibling modules:

```text
packages/core/megaloader/
├── __init__.py           public exports
├── api.py                extract()
├── plugin.py             BasePlugin contract
├── fetcher.py            Request, Response, and RequestsFetcher
├── item.py               DownloadItem metadata
├── filenames.py          filename derivation
├── exceptions.py         public exception types
├── error_policy.py       failure classification and construction
└── plugins/
    ├── registry.py       domain and name lookup
    └── <platform>.py     one plugin per platform
```

`extract()` in `api.py` resolves a plugin and passes it the fetcher. The modules
above are siblings in the package, not children of that function.

Plugins describe requests as `Request` values and read `Response` values from
the `Fetcher` passed to them. `RequestsFetcher` is the production implementation
that owns the session, timeout, retries, headers, and request failures. Tests
can provide a fetcher backed by recorded or hand-written responses.

`plugins/registry.py` holds the domain and plugin-name registries, plus the
subdomain rules. The CLI's `plugins` command and the API's domain check use
these registries. `extract()` preserves expected extraction errors and wraps
unexpected plugin exceptions as `ExtractionError(category="unknown")`.

`error_policy.py` builds `ExtractionError` values and assigns their categories.
`exceptions.py` defines the public exception types. A plugin reports an
unexpected response through `build_extraction_error()` or
`raise_extraction_error()`.

## CLI

```text
packages/cli/megaloader_cli/
├── main.py       click group, options, and the plugins command
├── commands.py   extraction, filtering, and download orchestration
├── io.py         streaming file downloads and progress updates
└── utils.py      console, logging, and filesystem-safe names
```

The CLI calls `megaloader.extract()`. Its `extract` command prints metadata; its
`download` command sends each item's URL and headers with `requests`, applies
`--filter` and `--flat`, and reports failures through its exit status.

## API

`apps/api/index.py` defines `/`, `/validate`, and `/download`. The modules under
`apps/api/api/` own the boundaries around those routes:

| Module          | Responsibility                                       |
| --------------- | ---------------------------------------------------- |
| `config.py`     | Environment variables and logging                    |
| `security.py`   | Domain checks, public-address checks, and rate limit |
| `safe_http.py`  | Redirect-following public download streams           |
| `extraction.py` | Core extraction and error-to-status mapping          |
| `downloads.py`  | Temporary files and the streaming size budget        |
| `responses.py`  | Single-file and ZIP responses                        |
| `models.py`     | Request and response models                          |
| `formatters.py` | Log formatting                                       |
| `utils.py`      | Size formatting and `HEAD` size checks               |

The API checks the caller and source domain before extraction. It checks file
sizes with `HEAD`, then enforces the size budget again while streaming each
download.

## Manual and tests

`apps/docs/megaloader/` contains the manual pages. Its `readme.md` is rewritten
to the site root by `.vitepress/config.mts`; the API demo component reads
`VITE_API_URL` and falls back to `http://localhost:8000`.

Core unit tests use hand-written responses through `fake_fetcher`. Plugin tests
replay recorded HTTP exchanges and compare normalised items with snapshots. API
tests are in `apps/api/tests/`; script tests are in `scripts/script_tests/`. See
[Testing plugins](../apps/docs/megaloader/testing-plugins.md) for the plugin
test boundary.

[`scripts/`](../scripts/readme.md) contains the logo generator, tool-version
updater, and snippet validator. `mise.toml` exposes the commands that run them.
