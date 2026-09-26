import pytest


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1/x",
        "http://127.1/x",
        "http://2130706433/x",
        "http://localhost:8080/x",
        "http://10.0.0.5/x",
        "http://172.16.0.1/x",
        "http://192.168.1.1/x",
        "http://169.254.169.254/latest/meta-data/",
        "http://100.64.0.1/x",
        "http://0.0.0.0/x",
        "http://[::1]/x",
        "http://[::ffff:127.0.0.1]/x",
        "http://[fe80::1]/x",
        "http://[fd00::1]/x",
        "http://224.0.0.1/x",
        "ftp://93.184.216.34/x",
        "file:///etc/passwd",
        "http:///x",
        "http://a..b/x",
        f"http://{'a' * 70}.example/x",
    ],
)
def test_non_public_or_non_http_urls_are_refused(url: str) -> None:
    from api.security import NonPublicURLError, ensure_public_url

    with pytest.raises(NonPublicURLError):
        ensure_public_url(url)


@pytest.mark.parametrize(
    "url",
    [
        "http://93.184.216.34/x",
        "https://93.184.216.34:8443/x",
        "http://[2606:2800:220:1:248:1893:25c8:1946]/x",
    ],
)
def test_public_addresses_are_allowed(url: str) -> None:
    from api.security import ensure_public_url

    ensure_public_url(url)


def test_unresolvable_host_is_refused() -> None:
    from api.security import NonPublicURLError, ensure_public_url

    with pytest.raises(NonPublicURLError, match="resolve"):
        ensure_public_url("http://does-not-exist.invalid/x")
