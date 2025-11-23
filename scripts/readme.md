# Scripts

Utility scripts for the Megaloader project.

## generate-logo.py

Generates the project logo as an SVG.

```bash
mise run generate-logo
```

Outputs `assets/logo.svg` in the root directory.

## validate-code-snippets.py

Validates Python code snippets in documentation files for syntax correctness.

```bash
python scripts/validate-code-snippets.py
```

Scans all markdown files in `docs/` and validates Python code blocks. Only Python code blocks are considered; other block types (e.g., Bash, PowerShell, JSON) are ignored.
- Blocks containing `...` (placeholders)
- Function/method signatures without bodies

Exits with code 0 if all snippets are valid, 1 if syntax errors are found.

## Future scripts

- Version updater: Automated tool to update Python, biome, and other version references across the repo.

