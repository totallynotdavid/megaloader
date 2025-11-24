#!/usr/bin/env python3
"""Validate Python code snippets in documentation files.

This script validates syntax only using ast.parse(). Code is not executed,
so imports don't need to resolve and variables don't need to exist. Only
checks that Python can parse the code as valid syntax.

Skipped code blocks:
- Blocks containing '...' (ellipsis placeholders)
- Function/method signatures without bodies (e.g., 'def foo() -> None')
- Bash, PowerShell, and JSON code blocks (non-Python languages)

Valid blocks are parsed but never executed, making validation safe and fast.
"""

import ast
import re
import sys

from pathlib import Path


def find_markdown_files(docs_dir: Path) -> list[Path]:
    """Find all markdown files in the docs directory."""
    return sorted(docs_dir.rglob("*.md"))


def extract_python_blocks(content: str) -> list[tuple[str, int]]:
    """
    Extract Python code blocks with their starting line numbers.
    Supports VitePress syntax highlighting (e.g., python{16} or python{1,3-5}).

    Returns list of (code, line_number) tuples.
    """
    blocks = []
    # Match: ```python or ```python{16} or ```python{1,3-5}
    pattern = r"```python(?:\{[\d,\-]+\})?\n(.*?)```"

    for match in re.finditer(pattern, content, re.DOTALL):
        code = match.group(1)
        line_number = content[: match.start()].count("\n") + 1
        blocks.append((code, line_number))

    return blocks


def should_skip_block(code: str) -> bool:
    """Determine if a code block should be skipped."""
    if "..." in code:
        return True

    lines = [line.rstrip() for line in code.split("\n")]

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        # Skip function/method signatures without bodies
        if stripped.startswith("def ") and not stripped.endswith(":"):
            return True

    return False


def validate_python_syntax(code: str) -> tuple[bool, str]:
    """
    Check if code has valid Python syntax.

    Returns (is_valid, error_message) tuple.
    """
    try:
        ast.parse(code)
        return True, ""
    except SyntaxError as e:
        return False, e.msg


def format_error(filepath: Path, line_number: int, message: str) -> str:
    """Format error message with file location."""
    return f"{filepath}:{line_number}: {message}"


def validate_file(filepath: Path) -> list[str]:
    """
    Validate all Python blocks in a file.

    Returns list of error messages.
    """
    content = filepath.read_text(encoding="utf-8")
    blocks = extract_python_blocks(content)
    errors = []

    for code, line_number in blocks:
        if should_skip_block(code):
            continue

        is_valid, error_message = validate_python_syntax(code)
        if not is_valid:
            errors.append(format_error(filepath, line_number, error_message))

    return errors


def main() -> int:
    """Run validation on all documentation files."""
    docs_dir = Path("apps/docs")

    if not docs_dir.exists():
        print(f"Error: {docs_dir} directory not found", file=sys.stderr)
        return 1

    markdown_files = find_markdown_files(docs_dir)
    all_errors = []
    files_with_errors = 0

    for filepath in markdown_files:
        errors = validate_file(filepath)
        if errors:
            files_with_errors += 1
        all_errors.extend(errors)

    if all_errors:
        print(f"Found {len(all_errors)} syntax errors in {files_with_errors} files:\n")
        for error in all_errors:
            print(error)
        return 1

    print(f"All Python code snippets are valid (checked {len(markdown_files)} files)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
