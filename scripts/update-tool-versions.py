#!/usr/bin/env python3
"""Update tool versions across the repository.

This script updates version numbers for tools and dependencies using
pattern-based matching. It avoids hardcoding line numbers and works
reliably even as files change.

Supported tools:
- Python (exact version and minimum version)
- uv, ruff, bun, biome (mise.toml)
- GitHub Actions (with SHA comments)
- Python dev dependencies (mypy, pytest)

Usage:
    python scripts/update-tool-versions.py --tool python --version 3.14.0
    python scripts/update-tool-versions.py --tool uv --version 0.10.0
    python scripts/update-tool-versions.py --dry-run
"""

import argparse
import re
import sys

from pathlib import Path
from typing import NamedTuple


class VersionUpdate(NamedTuple):
    """Represents a version update operation."""

    file_path: Path
    pattern: str
    replacement: str
    description: str


class ToolVersionUpdater:
    """Update tool versions across repository files."""

    def __init__(self, repo_root: Path, dry_run: bool = False) -> None:  # noqa: FBT001, FBT002
        self.repo_root = repo_root
        self.dry_run = dry_run
        self.updates: list[VersionUpdate] = []

    def update_python_exact(self, new_version: str) -> None:
        """Update exact Python version (3.13.7 format)."""
        files_to_update = [
            (self.repo_root / ".python-version", r"^\d+\.\d+\.\d+$", new_version),
            (
                self.repo_root / "mise.toml",
                r'python = "\d+\.\d+\.\d+"',
                f'python = "{new_version}"',
            ),
            (
                self.repo_root / ".github/workflows/release-core.yml",
                r'python-version: "\d+\.\d+\.\d+"',
                f'python-version: "{new_version}"',
            ),
            (
                self.repo_root / ".github/workflows/release-cli.yml",
                r'python-version: "\d+\.\d+\.\d+"',
                f'python-version: "{new_version}"',
            ),
        ]

        for file_path, pattern, replacement in files_to_update:
            self.updates.append(
                VersionUpdate(
                    file_path=file_path,
                    pattern=pattern,
                    replacement=replacement,
                    description=f"Python exact version in {file_path.name}",
                )
            )

    def update_python_minimum(self, new_minimum: str) -> None:
        """Update minimum Python version (>=3.10 format)."""
        pyproject_files = [
            self.repo_root / "pyproject.toml",
            self.repo_root / "packages/core/pyproject.toml",
            self.repo_root / "packages/cli/pyproject.toml",
            self.repo_root / "packages/api/pyproject.toml",
        ]

        for file_path in pyproject_files:
            self.updates.append(
                VersionUpdate(
                    file_path=file_path,
                    pattern=r'requires-python = ">=\d+\.\d+"',
                    replacement=f'requires-python = ">={new_minimum}"',
                    description=f"Python minimum version in {file_path.name}",
                )
            )

        self.updates.append(
            VersionUpdate(
                file_path=self.repo_root / "pyproject.toml",
                pattern=r'target-version = "py\d+"',
                replacement=f'target-version = "py{new_minimum.replace(".", "")}"',
                description="Ruff target version",
            )
        )

    def update_python_test_matrix(self, versions: list[str]) -> None:
        """Update Python test matrix versions."""
        versions_str = '", "'.join(versions)

        self.updates.append(
            VersionUpdate(
                file_path=self.repo_root / ".github/workflows/test.yml",
                pattern=r'python-version: \["[\d.]+",\s*"[\d.]+"\]',
                replacement=f'python-version: ["{versions_str}"]',
                description="Python test matrix",
            )
        )

    def update_mise_tool(self, tool: str, new_version: str) -> None:
        """Update a tool version in mise.toml (uv, ruff, bun, biome)."""
        self.updates.append(
            VersionUpdate(
                file_path=self.repo_root / "mise.toml",
                pattern=rf'{tool} = "[\d.]+"',
                replacement=f'{tool} = "{new_version}"',
                description=f"{tool} in mise.toml",
            )
        )

    def update_uv_in_actions(self, new_version: str) -> None:
        """Update uv version in GitHub Actions workflows."""
        workflow_files = [
            ".github/workflows/test.yml",
            ".github/workflows/release-core.yml",
            ".github/workflows/release-cli.yml",
            ".github/workflows/checks.yml",
        ]

        for workflow_file in workflow_files:
            self.updates.append(
                VersionUpdate(
                    file_path=self.repo_root / workflow_file,
                    pattern=r'version: "[\d.]+"',
                    replacement=f'version: "{new_version}"',
                    description=f"uv version in {Path(workflow_file).name}",
                )
            )

    def update_python_dev_dependency(self, package: str, new_version: str) -> None:
        """Update Python dev dependency minimum version (mypy, pytest)."""
        self.updates.append(
            VersionUpdate(
                file_path=self.repo_root / "packages/core/pyproject.toml",
                pattern=rf'"{package}>=[\d.]+"',
                replacement=f'"{package}>={new_version}"',
                description=f"{package} minimum version",
            )
        )

    def apply_updates(self) -> int:
        """Apply all queued updates."""
        if not self.updates:
            print("No updates to apply")
            return 0

        files_updated = set()
        errors = []

        for update in self.updates:
            try:
                if not update.file_path.exists():
                    errors.append(f"File not found: {update.file_path}")
                    continue

                content = update.file_path.read_text(encoding="utf-8")
                new_content = re.sub(
                    update.pattern, update.replacement, content, flags=re.MULTILINE
                )

                if content == new_content:
                    print(f"  No match: {update.description}")
                    continue

                if self.dry_run:
                    print(f"  Would update: {update.description}")
                    files_updated.add(update.file_path)
                else:
                    update.file_path.write_text(new_content, encoding="utf-8")
                    print(f"  Updated: {update.description}")
                    files_updated.add(update.file_path)

            except OSError as e:
                errors.append(f"Error updating {update.file_path}: {e}")

        print(
            f"\n{len(files_updated)} files {'would be ' if self.dry_run else ''}updated"
        )

        if errors:
            print("\nErrors encountered:")
            for error in errors:
                print(f"  {error}")
            return 1

        return 0


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Update tool versions across the repository"
    )

    parser.add_argument(
        "--tool",
        choices=[
            "python",
            "python-min",
            "python-matrix",
            "uv",
            "ruff",
            "bun",
            "biome",
            "mypy",
            "pytest",
        ],
        help="Tool to update",
    )

    parser.add_argument("--version", help="New version number")

    parser.add_argument(
        "--matrix-versions",
        help='Python matrix versions (comma-separated, e.g., "3.12,3.13")',
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be updated without making changes",
    )

    return parser.parse_args()


def main() -> int:  # noqa: C901
    """Main entry point."""
    args = parse_arguments()

    if not args.tool and not args.dry_run:
        print("Error: --tool is required unless using --dry-run")
        return 1

    repo_root = Path(__file__).parent.parent
    updater = ToolVersionUpdater(repo_root, dry_run=args.dry_run)

    if args.dry_run:
        print("Dry run mode - no files will be modified\n")

    if args.tool == "python":
        if not args.version:
            print("Error: --version required for Python update")
            return 1
        print(f"Updating Python exact version to {args.version}...\n")
        updater.update_python_exact(args.version)

    elif args.tool == "python-min":
        if not args.version:
            print("Error: --version required for Python minimum update")
            return 1
        print(f"Updating Python minimum version to >={args.version}...\n")
        updater.update_python_minimum(args.version)

    elif args.tool == "python-matrix":
        if not args.matrix_versions:
            print("Error: --matrix-versions required for Python matrix update")
            return 1
        versions = [v.strip() for v in args.matrix_versions.split(",")]
        print(f"Updating Python test matrix to {versions}...\n")
        updater.update_python_test_matrix(versions)

    elif args.tool == "uv":
        if not args.version:
            print("Error: --version required for uv update")
            return 1
        print(f"Updating uv to {args.version}...\n")
        updater.update_mise_tool("uv", args.version)
        updater.update_uv_in_actions(args.version)

    elif args.tool in ("ruff", "bun", "biome"):
        if not args.version:
            print(f"Error: --version required for {args.tool} update")
            return 1
        print(f"Updating {args.tool} to {args.version}...\n")
        updater.update_mise_tool(args.tool, args.version)

    elif args.tool in ("mypy", "pytest"):
        if not args.version:
            print(f"Error: --version required for {args.tool} update")
            return 1
        print(f"Updating {args.tool} minimum to >={args.version}...\n")
        updater.update_python_dev_dependency(args.tool, args.version)

    return updater.apply_updates()


if __name__ == "__main__":
    sys.exit(main())
