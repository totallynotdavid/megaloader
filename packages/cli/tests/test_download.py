import threading

from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from click.testing import CliRunner
from megaloader.item import DownloadItem
from rich.console import Console
from rich.progress import Progress

from megaloader_cli import commands
from megaloader_cli.io import download_file
from megaloader_cli.main import cli
from megaloader_cli.utils import sanitize_for_filesystem


LOOPBACK = pytest.mark.block_network(allowed_hosts=["127.0.0.1"])

BODIES = {
    "/first": b"first body",
    "/second": b"second body",
    "/large": b"x" * 64 * 1024,
}


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        body = BODIES[self.path]
        self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        pass


@pytest.fixture
def base_url() -> Iterator[str]:
    server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()
    server.server_close()
    thread.join()


def _serve_items(monkeypatch: pytest.MonkeyPatch, items: list[DownloadItem]) -> None:
    monkeypatch.setattr(commands.mgl, "extract", lambda *_a, **_k: iter(items))


def _tree(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("plain.jpg", "plain.jpg"),
        ("a<b>c:d.jpg", "a_b_c_d.jpg"),
        ("..", "unnamed"),
        (".", "unnamed"),
        ("...", "unnamed"),
        ("name. ", "name"),
        ("tab\tand\nnewline", "tab_and_newline"),
        ("CON", "_CON"),
        ("nul.txt", "_nul.txt"),
        ("console.txt", "console.txt"),
        (".hidden", ".hidden"),
        ("", "unnamed"),
    ],
)
def test_sanitized_name_cannot_leave_or_break_its_directory(
    name: str, expected: str
) -> None:
    assert sanitize_for_filesystem(name) == expected


@LOOPBACK
def test_collection_named_as_a_dot_segment_stays_inside_the_output_dir(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, base_url: str
) -> None:
    _serve_items(
        monkeypatch,
        [DownloadItem(base_url + "/first", "a.txt", collection_name="..")],
    )
    out = tmp_path / "out"

    result = CliRunner().invoke(cli, ["download", "https://example.com/x", str(out)])

    assert result.exit_code == 0, result.output
    assert _tree(tmp_path) == {"out/unnamed/a.txt": b"first body"}


@LOOPBACK
def test_files_that_share_a_name_are_all_kept(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, base_url: str
) -> None:
    _serve_items(
        monkeypatch,
        [
            DownloadItem(base_url + "/first", "same.txt"),
            DownloadItem(base_url + "/second", "same.txt"),
            DownloadItem(base_url + "/second", "sa?me.txt"),
        ],
    )

    result = CliRunner().invoke(
        cli, ["download", "https://example.com/x", str(tmp_path)]
    )

    assert result.exit_code == 0, result.output
    assert _tree(tmp_path) == {
        "same.txt": b"first body",
        "same (2).txt": b"second body",
        "sa_me.txt": b"second body",
    }


def test_markup_in_a_filename_is_printed_verbatim(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _serve_items(
        monkeypatch,
        [DownloadItem("https://example.com/a", "[hd] clip.mp4", collection_name="[x]")],
    )

    result = CliRunner().invoke(cli, ["extract", "https://example.com/x"])

    assert "[hd] clip.mp4" in result.output
    assert "Collection: [x]" in result.output


class _InterruptedProgress(Progress):
    def advance(self, task_id, advance: float = 1) -> None:  # type: ignore[no-untyped-def]
        super().advance(task_id, advance)
        if advance > 100:
            raise KeyboardInterrupt


@LOOPBACK
def test_interrupted_download_leaves_nothing_to_skip_next_time(
    tmp_path: Path, base_url: str
) -> None:
    item = DownloadItem(base_url + "/large", "big.bin")
    destination = tmp_path / "big.bin"
    progress = _InterruptedProgress(console=Console(quiet=True))
    task = progress.add_task("download", start=False)

    with pytest.raises(KeyboardInterrupt):
        download_file(item, destination, progress, task)

    assert list(tmp_path.iterdir()) == []

    retry = Progress(console=Console(quiet=True))
    retry_task = retry.add_task("download", start=False)
    assert download_file(item, destination, retry, retry_task)
    assert destination.read_bytes() == BODIES["/large"]


@pytest.mark.parametrize(
    "url",
    [
        "https://pixeldrain.com:443/u/abc",
        "https://user@pixeldrain.com/u/abc",
        "https://PixelDrain.com/u/abc",
    ],
)
def test_extract_names_the_plugin_from_the_host_alone(
    monkeypatch: pytest.MonkeyPatch, url: str
) -> None:
    monkeypatch.setattr(commands.mgl, "extract", lambda *_a, **_k: iter(()))

    result = CliRunner().invoke(cli, ["extract", url])

    assert "Using plugin: PixelDrain" in result.output
