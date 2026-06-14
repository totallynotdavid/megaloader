from collections.abc import Mapping

from megaloader.fetcher import Fetcher, Request, Response
from megaloader.item import DownloadItem


def fake_fetcher(routes: Mapping[str, Response | str | BaseException]) -> Fetcher:
    """Build a Fetcher that serves canned outcomes by request URL.

    Lets a plugin's traversal run offline: map each URL it will request to a
    body (a str becomes a 200 with that text), a Response for full control, or
    an exception to inject a fault (e.g. an ExtractionError to exercise the
    404-stops-pagination path). An unmapped URL fails loudly so missing fixtures
    surface as test errors rather than silent network access.
    """

    def fetch(request: Request) -> Response:
        if request.url not in routes:
            msg = f"unexpected request to {request.url}"
            raise AssertionError(msg)

        value = routes[request.url]
        if isinstance(value, BaseException):
            raise value
        if isinstance(value, Response):
            return value
        return Response(
            url=request.url,
            status_code=200,
            text=value,
            content=value.encode(),
        )

    return fetch


def assert_valid_item(item: DownloadItem) -> None:
    """Reject items with an unusable URL scheme or an unsafe, non-leaf filename."""
    assert item.download_url.startswith(("http://", "https://")), (
        f"Invalid URL schema: {item.download_url}"
    )
    assert item.filename, "Filename cannot be empty"
    assert ".." not in item.filename, "Filename contains path traversal"
    assert "/" not in item.filename, "Filename contains directory separators"
