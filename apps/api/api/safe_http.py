from urllib.parse import urljoin, urlparse

import requests

from api import security


MAX_REDIRECTS = 5

DEFAULT_PORTS = {"http": 80, "https": 443}

# Sent to the origin the item was extracted for, never forwarded to another one.
CREDENTIAL_HEADERS = frozenset({"authorization", "cookie"})


def open_public_stream(
    method: str, url: str, headers: dict[str, str], timeout: float
) -> requests.Response:
    """
    Send a request and follow redirects by hand, refusing any hop that does not
    lead to a public host. The caller closes the returned response.

    Raises security.NonPublicURLError, requests.TooManyRedirects or any other
    requests.RequestException.
    """
    for _ in range(MAX_REDIRECTS + 1):
        security.ensure_public_url(url)

        response = requests.request(
            method,
            url,
            headers=headers,
            timeout=timeout,
            stream=True,
            allow_redirects=False,
        )
        if not response.is_redirect:
            return response

        target = urljoin(url, response.headers["Location"])
        response.close()
        headers = headers_for_hop(headers, url, target)
        url = target

    msg = f"Exceeded {MAX_REDIRECTS} redirects"
    raise requests.TooManyRedirects(msg)


def headers_for_hop(
    headers: dict[str, str], source: str, target: str
) -> dict[str, str]:
    if keeps_credentials(source, target):
        return headers
    return {
        name: value
        for name, value in headers.items()
        if name.lower() not in CREDENTIAL_HEADERS
    }


def keeps_credentials(source: str, target: str) -> bool:
    """
    Credentials follow a redirect only within one origin (scheme, host and port),
    plus the http to https upgrade on default ports, as in requests.
    """
    old, new = urlparse(source), urlparse(target)
    if old.hostname != new.hostname:
        return False

    origin = (old.scheme, old.port or DEFAULT_PORTS.get(old.scheme))
    upgraded = (new.scheme, new.port or DEFAULT_PORTS.get(new.scheme))
    return origin == upgraded or (origin, upgraded) == (("http", 80), ("https", 443))
