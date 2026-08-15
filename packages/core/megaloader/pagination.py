import logging

from collections.abc import Callable, Generator

from megaloader.exceptions import ExtractionError
from megaloader.fetcher import Fetcher, Request, Response


logger = logging.getLogger(__name__)


def crawl_pages(
    fetch: Fetcher,
    request_for_page: Callable[[int], Request],
    *,
    start: int = 1,
    step: int = 1,
    stop_statuses: tuple[int, ...] = (),
) -> Generator[Response, None, None]:
    """Yield successive listing pages until the site runs out of them.

    Walks page numbers from start in increments of step, stopping on an empty
    response body or on one of stop_statuses (sites that answer past-the-end
    pages with 404 instead of an empty body). Callers stop early by breaking out
    of the loop when a page holds no items they can use.
    """
    page = start
    while True:
        try:
            response = fetch(request_for_page(page))
        except ExtractionError as e:
            if e.http_status in stop_statuses:
                return
            raise

        if not response.text.strip():
            return

        yield response
        page += step
