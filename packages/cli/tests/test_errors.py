from collections.abc import Iterator

import pytest

from click.testing import CliRunner
from megaloader.item import DownloadItem
from megaloader_cli import commands
from megaloader_cli.main import cli


@pytest.mark.parametrize("command", ["extract", "download"])
@pytest.mark.parametrize(
    "url",
    [
        "https://bunkr.si/v/something",
        "https://www.pixiv.net/",
    ],
)
def test_invalid_url_prints_error_without_traceback(command: str, url: str) -> None:
    result = CliRunner().invoke(cli, [command, url])

    assert result.exit_code == 1
    assert "Error:" in result.output
    assert "Traceback" not in result.output
    assert isinstance(result.exception, SystemExit)


def _one_item(*_args: object, **_kwargs: object) -> Iterator[DownloadItem]:
    yield DownloadItem(download_url="https://example.com/a.jpg", filename="a.jpg")


def _explode(*_args: object, **_kwargs: object) -> None:
    msg = "unrelated bug"
    raise ValueError(msg)


# Extraction is network-bound, so the extractor is replaced; the point is that a
# ValueError raised after extraction is not swallowed as a user-facing error.
@pytest.mark.parametrize(
    ("command", "failing_step"),
    [("extract", "_print_human_readable"), ("download", "_download_with_progress")],
)
def test_value_error_after_extraction_keeps_its_traceback(
    monkeypatch: pytest.MonkeyPatch, command: str, failing_step: str
) -> None:
    monkeypatch.setattr(commands.mgl, "extract", _one_item)
    monkeypatch.setattr(commands, failing_step, _explode)

    result = CliRunner().invoke(cli, [command, "https://example.com/a"])

    assert isinstance(result.exception, ValueError)
    assert "Error:" not in result.output
