from collections.abc import Mapping

from megaloader.fetcher import Fetcher, Request, Response


def fake_fetcher(routes: Mapping[str, Response | str | BaseException]) -> Fetcher:
    """Build a Fetcher that serves canned outcomes by request URL.

    A str becomes a 200 with that text, a Response is returned as is, and an
    exception is raised. An unmapped URL fails the test.
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
