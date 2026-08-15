from collections.abc import Iterable, Iterator
from typing import overload
from urllib.parse import urljoin

from bs4 import BeautifulSoup, PageElement


def parse_html(page: str) -> BeautifulSoup:
    """Parse markup with the parser every plugin uses."""
    return BeautifulSoup(page, "html.parser")


@overload
def element_text(element: PageElement | None, default: str) -> str: ...


@overload
def element_text(element: PageElement | None, default: None = None) -> str | None: ...


def element_text(element: PageElement | None, default: str | None = None) -> str | None:
    """Return an element's stripped text, or the default when it is missing."""
    if element is None:
        return default
    return element.text.strip() or default


def unique(values: Iterable[str]) -> Iterator[str]:
    """Yield values in order, skipping ones already seen."""
    seen: set[str] = set()
    for value in values:
        if value not in seen:
            seen.add(value)
            yield value


def absolute_links(soup: BeautifulSoup, selector: str, base_url: str) -> list[str]:
    """Return absolute, de-duplicated hrefs of matching elements, in page order."""
    return list(
        unique(
            urljoin(base_url, str(href))
            for link in soup.select(selector)
            if (href := link.get("href"))
        )
    )
