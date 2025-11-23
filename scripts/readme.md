# Scripts

Utility scripts used throughout the Megaloader project.

## generate-logo.py

Generates the project logo as an SVG.

```bash
mise run generate-logo
```

The script outputs `assets/logo.svg` at the repository root.

## validate-code-snippets.py

Validates Python code snippets in documentation files for syntax correctness.

```bash
python scripts/validate-code-snippets.py
```

The script scans all Markdown files in `docs/` and checks **only Python** code
blocks. Other languages (Bash, PowerShell, JSON, etc.) are ignored. Certain
patterns are intentionally skipped:

- Blocks containing placeholder `...`
- Function or method signatures without bodies

The script exits with:

- **0** if all snippets are valid
- **1** if any syntax errors are found

## update-tool-versions.py

Updates tool versions across the repository using pattern-based matching.

```bash
# Update Python exact version (3.13.7 -> 3.14.0)
python scripts/update-tool-versions.py --tool python --version 3.14.0

# Update Python minimum requirement (>=3.10 -> >=3.11)
python scripts/update-tool-versions.py --tool python-min --version 3.11

# Update Python test matrix
python scripts/update-tool-versions.py --tool python-matrix --matrix-versions "3.13,3.14"

# Update development tools
python scripts/update-tool-versions.py --tool uv --version 0.10.0
python scripts/update-tool-versions.py --tool ruff --version 0.15.0
python scripts/update-tool-versions.py --tool mypy --version 1.19.0

# Dry run to preview changes
python scripts/update-tool-versions.py --tool python --version 3.14.0 --dry-run
```

**Supported tools:** `python`, `python-min`, `python-matrix`, `uv`, `ruff`,
`bun`, `biome`, `mypy`, `pytest`

The script updates:

- `.python-version` and `mise.toml` tool versions
- All `pyproject.toml` files for Python requirements
- GitHub Actions workflows for CI/CD version consistency
- Tooling configuration across the monorepo to ensure aligned versions
