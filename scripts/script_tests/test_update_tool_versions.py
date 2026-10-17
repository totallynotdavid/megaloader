import importlib.util
import shutil
import subprocess
import sys

from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts/update-tool-versions.py"


@pytest.fixture
def repo_copy(tmp_path: Path) -> Path:
    # copyfile drops the source mode, so read-only checkouts still yield writable copies.
    shutil.copyfile(REPO_ROOT / "mise.toml", tmp_path / "mise.toml")
    shutil.copytree(
        REPO_ROOT / ".github/workflows",
        tmp_path / ".github/workflows",
        copy_function=shutil.copyfile,
    )
    for relative_path in (
        Path("packages/core/pyproject.toml"),
        Path("apps/api/pyproject.toml"),
    ):
        destination = tmp_path / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPO_ROOT / relative_path, destination)
    return tmp_path


def load_updater_class() -> type:
    spec = importlib.util.spec_from_file_location("update_tool_versions", SCRIPT)
    assert spec
    assert spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.ToolVersionUpdater


def update_tool(repo: Path, tool: str, version: str) -> None:
    updater = load_updater_class()(repo)
    updater.update_mise_tool(tool, version)
    assert updater.apply_updates() == 0


def update_python_dependency(repo: Path, package: str, version: str) -> None:
    updater = load_updater_class()(repo)
    updater.update_python_dev_dependency(package, version)
    assert updater.apply_updates() == 0


def changed_lines(repo: Path) -> dict[str, list[str]]:
    changes = {}
    tracked = [Path("mise.toml")]
    for name in tracked:
        old = (REPO_ROOT / name).read_text().splitlines()
        new = (repo / name).read_text().splitlines()
        assert len(old) == len(new)
        diff = [b.strip() for a, b in zip(old, new, strict=True) if a != b]
        if diff:
            changes[str(name)] = diff
    return changes


def test_ruff_bump_changes_only_ruff_lines(repo_copy: Path) -> None:
    update_tool(repo_copy, "ruff", "9.9.9")

    assert changed_lines(repo_copy) == {"mise.toml": ['ruff = "9.9.9"']}


def test_uv_bump_changes_only_uv_in_mise(repo_copy: Path) -> None:
    update_tool(repo_copy, "uv", "9.9.9")

    changes = changed_lines(repo_copy)
    assert changes["mise.toml"] == ['uv = "9.9.9"']


def test_cli_dry_run_reports_ruff_updates_without_writing() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--tool",
            "ruff",
            "--version",
            "9.9.9",
            "--dry-run",
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    assert "Would update: ruff in mise.toml" in result.stdout


def test_python_dev_dependency_bump_updates_every_python_project(
    repo_copy: Path,
) -> None:
    update_python_dependency(repo_copy, "pytest", "9.9.9")

    for relative_path in (
        Path("packages/core/pyproject.toml"),
        Path("apps/api/pyproject.toml"),
    ):
        content = (repo_copy / relative_path).read_text()
        assert '"pytest>=9.9.9"' in content
