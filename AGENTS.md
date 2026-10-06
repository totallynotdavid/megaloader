# AGENTS.md

Megaloader finds the downloadable files behind a hosting-site link. Read
[`architecture.md`](architecture.md) for the code map and
[`.github/CONTRIBUTING.md`](.github/CONTRIBUTING.md) for the workflow.

## Rules

- Run `mise run check` and `mise run test` before finishing. `check` formats
  code, so commit what it changes.
- Keep Python 3.10 compatibility in `packages/core` and `packages/cli`.
- Run API commands through the mise tasks, which clear `VIRTUAL_ENV`.
- A plugin does no network I/O. It sends every request through the `fetch`
  argument of `extract()`.
- Raise plugin failures with `raise_extraction_error` or
  `build_extraction_error` from `megaloader.error_policy`.
- Register a new plugin in both `PLUGIN_REGISTRY` and `PLUGIN_NAME_REGISTRY` in
  `packages/core/megaloader/plugins/registry.py`.
- A new plugin comes with entries in `packages/core/tests/test_urls.py`, a
  `tests/plugins/test_<plugin>.py` module, and rows in
  `apps/docs/megaloader/platforms.md` and `plugin-options.md`.
- Tests in `packages/core/tests/plugins/` replay recorded cassettes.
  Hand-written input goes in `packages/core/tests/unit/` through `fake_fetcher`.
- Run offline tests with `--block-network`.
- Run `--record-mode=rewrite` only when asked. Commit cassettes and snapshots
  together.
- Never commit `.env` or credentials.
- Format Markdown with
  `bunx prettier --print-width 80 --prose-wrap always --write <file>`.
- A Python code block in `apps/docs` must parse. `mise run validate-snippets`
  checks it.
- Write commit messages as `area: imperative lowercase summary`.
