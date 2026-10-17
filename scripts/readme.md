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

Changes one tool's version in every file that pins it, including each Python
project that declares a supported development dependency. `--dry-run` shows the
changes without writing them.

```bash
python scripts/update-tool-versions.py --tool python --version 3.14.0
python scripts/update-tool-versions.py --tool python-min --version 3.11
python scripts/update-tool-versions.py --tool ruff --version 0.15.0 --dry-run
```

`--tool` takes `python`, `python-min`, `uv`, `ruff`, `bun`, `mypy`, or `pytest`.

`mise.toml` holds the Python, uv, ruff, and Bun versions. The docs lockfile
holds the JavaScript formatter and linter versions.

The script edits `mise.toml` and the `pyproject.toml` files. Its tests are in
`scripts/script_tests/` and run with `mise run test`.
