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
    if tool == "ruff":
        updater.update_mise_tool("ruff", version)
        updater.update_action_in_workflows("astral-sh/ruff-action", version)
    else:
        updater.update_mise_tool("uv", version)
        updater.update_action_in_workflows("astral-sh/setup-uv", version)
    assert updater.apply_updates() == 0


def changed_lines(repo: Path) -> dict[str, list[str]]:
    changes = {}
    workflows = sorted(REPO_ROOT.glob(".github/workflows/*.yml"))
    tracked = [Path("mise.toml"), *(w.relative_to(REPO_ROOT) for w in workflows)]
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

    assert changed_lines(repo_copy) == {
        "mise.toml": ['ruff = "9.9.9"'],
        ".github/workflows/checks.yml": ['version: "9.9.9"', 'version: "9.9.9"'],
    }


def test_uv_bump_leaves_ruff_action_version_alone(repo_copy: Path) -> None:
    update_tool(repo_copy, "uv", "9.9.9")

    changes = changed_lines(repo_copy)
    assert changes["mise.toml"] == ['uv = "9.9.9"']
    checks = (repo_copy / ".github/workflows/checks.yml").read_text()
    assert checks.count('version: "9.9.9"') == 1
    assert checks.count('version: "0.15.20"') == 2


def test_step_without_version_does_not_borrow_a_later_step(repo_copy: Path) -> None:
    workflow = repo_copy / ".github/workflows/checks.yml"
    text = workflow.read_text()
    workflow.write_text(
        text.replace(
            '        with:\n          version: "0.15.20"\n          args: "check"',
            '        with:\n          args: "check"',
        )
        + '      - uses: some/other-action@v1\n        with:\n          version: "1.0.0"\n'
    )

    update_tool(repo_copy, "ruff", "9.9.9")

    new_text = workflow.read_text()
    assert 'version: "1.0.0"' in new_text
    assert new_text.count('version: "9.9.9"') == 1


def test_cli_dry_run_reports_ruff_updates_without_writing() -> None:
    before = (REPO_ROOT / ".github/workflows/checks.yml").read_text()

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
    assert "Would update: astral-sh/ruff-action version in checks.yml" in result.stdout
    assert "setup-uv" not in result.stdout
    assert (REPO_ROOT / ".github/workflows/checks.yml").read_text() == before
