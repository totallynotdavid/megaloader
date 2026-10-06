# Architecture

Megaloader is a monorepo of four parts. The core library finds files. The CLI
and the API server are two front ends to it. The docs site is the manual.

| Path            | Package          | Role                                      |
| --------------- | ---------------- | ----------------------------------------- |
| `packages/core` | `megaloader`     | `extract()`, plugins, errors, the fetcher |
| `packages/cli`  | `megaloader-cli` | The `megaloader` command                  |
| `apps/api`      | `megaloader-api` | FastAPI server deployed to Vercel         |
| `apps/docs`     | none             | VitePress site, published to GitHub Pages |

`packages/core` and `packages/cli` form a uv workspace at the repository root.
`apps/api` is a separate uv project, so Vercel installs only its own
dependencies. `apps/docs` uses bun.

## Core

```text
packages/core/megaloader/
├── __init__.py       public exports
├── api.py            extract()
├── plugin.py         BasePlugin
├── fetcher.py        Fetcher, Request, Response, RequestsFetcher
├── item.py           DownloadItem
├── exceptions.py     MegaloaderError, ExtractionError, UnsupportedDomainError
├── error_policy.py   failure classification and ExtractionError construction
├── filenames.py      filename_from_url
└── plugins/
    ├── registry.py   domain and name registries, lookup functions
    └── <platform>.py one plugin per platform
```

### Flow of `extract()`

1. `extract()` validates the URL and picks a plugin class: from the `plugin`
   argument (a name or a class), or from the URL's host through
   `get_plugin_for_domain`. A host with no plugin raises
   `UnsupportedDomainError`.
2. It instantiates the plugin with the URL and the keyword options. The plugin
   validates the URL shape and raises `ValueError` for one it cannot read.
3. It builds a `RequestsFetcher` from the plugin's `source` and
   `session_config()`, plus the caller's `session` and `timeout`.
4. It yields from `plugin.extract(fetch)`. The call is a generator, so nothing
   runs until the caller iterates.
5. `ExtractionError`, `UnsupportedDomainError`, and `ValueError` pass through.
   Any other exception becomes `ExtractionError` with category `unknown`.

### The plugin and fetcher seam

A plugin never imports `requests`. It describes each request as a `Request`,
calls the `Fetcher` it was given, and reads a `Response`. `RequestsFetcher` is
the one implementation that touches the network. It owns the session, the
default `User-Agent`, the retry policy for sessions it builds, the timeout, and
the translation of every failed request into `ExtractionError`. Tests pass a
different `Fetcher`, so a plugin runs against canned responses with no mocking
of `requests`.

### Error policy

`error_policy.py` holds the rules that turn a status into a category.
`classify_failure` maps an HTTP status or a provider status to one of
`rate_limit`, `auth`, `access`, `request`, `network`, `timeout`, `protocol`, or
`unknown`. `build_extraction_error` and `raise_extraction_error` build the
exception, so a plugin never constructs `ExtractionError` by hand.

### Registries

`plugins/registry.py` holds `PLUGIN_REGISTRY` (domain to class),
`PLUGIN_NAME_REGISTRY` (name to class), and `SUBDOMAIN_SUPPORTED` (base domains
whose subdomains resolve to the same plugin). The CLI's `plugins` command and
the API's domain check read them.

## CLI

```text
packages/cli/megaloader_cli/
├── main.py       click group, option definitions, the plugins command
├── commands.py   the extract and download commands
├── io.py         download_file: streams one item to disk with progress
└── utils.py      console, logging setup, filename sanitising
```

The CLI calls `megaloader.extract()` and downloads each item with `requests`.
`commands.py` runs the extraction, applies `--filter` and `--flat`, and sets the
exit status.

## API

```text
apps/api/
├── index.py          FastAPI app and the three routes
└── api/
    ├── config.py     environment variables and logging
    ├── security.py   domain allow list, public-address check, rate limit
    ├── safe_http.py  redirect-following streams that re-check each hop
    ├── extraction.py calls megaloader, maps ExtractionError to HTTP status
    ├── downloads.py  size-budgeted downloads into a temporary directory
    ├── responses.py  single-file and ZIP responses
    ├── models.py     pydantic request and response models
    ├── formatters.py log formatter
    └── utils.py      size formatting and HEAD size checks
```

A request passes the rate limit, the domain allow list, and the public-address
check before `extract_items` runs. The size check sends a `HEAD` request for
each item, and the download enforces the limit again while streaming.

## Docs

`apps/docs/megaloader/` holds the Markdown pages and the VitePress config in
`.vitepress/`. `readme.md` is the manual index, and `config.mts` rewrites it to
the site root. `components/api-demo.vue` is the live demo on the Getting started
page and calls the API at `VITE_API_URL`, or `http://localhost:8000` when unset.

## Tests

```text
packages/core/tests/
├── unit/      hand-written input through fake_fetcher
├── plugins/   vcr cassettes and syrupy snapshots, one module per plugin
├── helpers.py fake_fetcher, assert_valid_item
└── test_urls.py  fixture URLs
packages/cli/tests/
apps/api/tests/
scripts/script_tests/
```

[Testing plugins](apps/docs/megaloader/testing-plugins.md) explains the two
styles and how recording works.

## Scripts and CI

[`scripts/`](scripts/readme.md) holds the logo generator, the tool version
updater, and the snippet validator. `mise.toml` defines the tasks that wrap
them, and `.github/workflows/` runs the same checks on pull requests:

| Workflow                     | Runs                                                          |
| ---------------------------- | ------------------------------------------------------------- |
| `checks.yml`                 | ruff format, ruff check, mypy, API tests                      |
| `test.yml`                   | Offline tests on Python 3.10, 3.12, 3.13, 3.14                |
| `live.yml`                   | Weekly re-recording of the plugin cassettes                   |
| `codeql.yml`, `security.yml` | CodeQL and PyCharm security scans                             |
| `deploy.yml`                 | Builds the docs site and publishes it to Pages                |
| `release-core.yml`           | Publishes `megaloader` to PyPI on a `vcore-*` tag             |
| `release-cli.yml`            | Publishes `megaloader-cli` and the binaries on a `vcli-*` tag |
