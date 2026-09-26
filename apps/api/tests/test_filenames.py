from collections.abc import Callable
from pathlib import Path
from types import ModuleType

import pytest

from megaloader.item import DownloadItem

from tests.servers import Route, Server


@pytest.mark.parametrize(
    ("filename", "expected"),
    [
        ("report.pdf", "report.pdf"),
        ("a/b.txt", "b.txt"),
        ("a\\b.txt", "b.txt"),
        ("x/../../escape.txt", "escape.txt"),
        ("..hidden", "..hidden"),
    ],
)
def test_filename_is_reduced_to_its_leaf(filename: str, expected: str) -> None:
    from api.downloads import safe_basename

    assert safe_basename(filename) == expected


@pytest.mark.parametrize(
    "filename",
    ["", ".", "..", "a/..", "a/", "/etc/passwd", "\\windows\\x", "a\0b"],
)
def test_unusable_filename_is_refused(filename: str) -> None:
    from api.downloads import UnsafeFilenameError, safe_basename

    with pytest.raises(UnsafeFilenameError):
        safe_basename(filename)


def unchecked_item(server: Server, filename: str) -> DownloadItem:
    """Build an item the way a plugin could: DownloadItem's own checks bypassed."""
    item = DownloadItem(download_url=server.base_url + "/f", filename="placeholder")
    item.filename = filename
    return item


@pytest.mark.parametrize("filename", ["../../escape.txt", "..\\..\\escape.txt"])
def test_traversal_writes_inside_the_output_dir(
    load_app: Callable[..., ModuleType],
    serve: Callable[..., Server],
    tmp_path: Path,
    filename: str,
) -> None:
    load_app()
    from api.downloads import download_file

    output_dir = tmp_path / "out"
    output_dir.mkdir()
    server = serve({"/f": Route(body=b"data")})

    written = download_file(unchecked_item(server, filename), output_dir, 1024)

    assert written == output_dir / "escape.txt"
    assert written.read_bytes() == b"data"
    assert sorted(p.name for p in tmp_path.rglob("*") if p.is_file()) == ["escape.txt"]


@pytest.mark.parametrize("filename", ["", "..", "/tmp/absolute.txt", "a\0b"])
def test_unsafe_filename_is_not_fetched_or_written(
    load_app: Callable[..., ModuleType],
    serve: Callable[..., Server],
    tmp_path: Path,
    filename: str,
) -> None:
    load_app()
    from api.downloads import download_file

    output_dir = tmp_path / "out"
    output_dir.mkdir()
    server = serve({"/f": Route(body=b"data")})

    written = download_file(unchecked_item(server, filename), output_dir, 1024)

    assert written is None
    assert server.hits == []
    assert list(tmp_path.rglob("*")) == [output_dir]
