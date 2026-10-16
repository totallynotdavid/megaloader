import pytest

from megaloader.item import DownloadItem


@pytest.mark.unit
def test_optional_fields_default_to_empty() -> None:
    item = DownloadItem(download_url="http://example.com/file.txt", filename="a.txt")

    assert item.collection_name is None
    assert item.source_id is None
    assert item.headers == {}
    assert item.size_bytes is None


@pytest.mark.unit
@pytest.mark.parametrize(
    ("download_url", "filename", "message"),
    [
        ("", "test.txt", "download_url cannot be empty"),
        ("http://example.com/file", "", "filename cannot be empty"),
        ("http://example.com/file", "folder/file.txt", "leaf name"),
        ("http://example.com/file", "folder\\file.txt", "leaf name"),
        ("http://example.com/file", "..file.txt", "path traversal"),
    ],
)
def test_rejects_unusable_fields(
    download_url: str, filename: str, message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        DownloadItem(download_url=download_url, filename=filename)
