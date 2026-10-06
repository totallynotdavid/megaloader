# Scripts

Run these from the repository root.

## generate-logo.py

Writes the project logo to `apps/docs/megaloader/public/logo.svg`.

```bash
mise run generate-logo
```

## validate-code-snippets.py

Parses every `python` code block in the Markdown files under `apps/docs` with
`ast.parse`. It checks syntax only and runs nothing. Blocks in other languages
are ignored, and so are blocks that contain `...` and function signatures with
no body. It exits 1 and lists the file and line of each syntax error.

```bash
mise run validate-snippets
```

On success it prints `All Python code snippets are valid` and the number of
files it checked.

## update-tool-versions.py

Changes one tool's version in every file that pins it. `--dry-run` shows the
changes without writing them.

```bash
python scripts/update-tool-versions.py --tool python --version 3.14.0
python scripts/update-tool-versions.py --tool python-min --version 3.11
python scripts/update-tool-versions.py --tool python-matrix --matrix-versions "3.13,3.14"
python scripts/update-tool-versions.py --tool ruff --version 0.15.0 --dry-run
```

`--tool` takes `python`, `python-min`, `python-matrix`, `uv`, `ruff`, `bun`,
`biome`, `mypy`, or `pytest`.

`mise.toml` holds the `uv` and `ruff` versions. Changing either also rewrites
the `version` input of `astral-sh/setup-uv` or `astral-sh/ruff-action` in
`.github/workflows/`, so CI uses the version used by `mise run format`.

The script edits `.python-version`, `mise.toml`, the `pyproject.toml` files, and
the workflows. Its tests are in `scripts/script_tests/` and run with
`mise run test-unit`.
