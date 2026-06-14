"""Proxy wiring for the plugin suite.

These tests replay committed cassettes offline by default, so the proxy is
dormant: no network, no credentials. It engages only when a recording mode is
active (`--record-mode=rewrite` to refresh cassettes, or the scheduled drift
run), where requests actually leave the machine.

The fixture is function scoped, so each test (each fixture URL) gets one fresh
Geonode port for the whole extraction it drives. That is the right grain: a
model traversal fans out into many independent page requests that spread across
IPs to dodge per-IP rate limits, while a single auth flow (gofile token, pixiv
session) stays pinned to one IP so its session state stays valid.

When a recording mode is active the proxy is mandatory: missing credentials
fail the run rather than silently hammering bare egress, which the target sites
block.
"""

import os

from collections.abc import Iterator

import pytest

from tests.plugins.proxy import credentials, missing_creds, proxy_url


_PROXY_ENV_VARS = ("HTTP_PROXY", "HTTPS_PROXY")


def _recording(config: pytest.Config) -> bool:
    """True when vcr will reach the network (any record mode other than none)."""
    mode = config.getoption("record_mode", default="none")
    return mode not in (None, "none")


# autouse is intentional: every plugin test must route through the proxy when
# recording, with no per-test opt-in. It is a no-op during offline replay.
@pytest.fixture(autouse=True)  # noqa: RUF076
def _rotating_proxy(request: pytest.FixtureRequest) -> Iterator[None]:
    """Route this test's requests through a fresh Geonode IP when recording."""
    if not _recording(request.config):
        yield
        return

    creds = credentials()
    if missing := missing_creds(creds):
        pytest.fail(f"recording requires proxy credentials, missing: {missing}")

    proxy = proxy_url(creds)
    saved = {var: os.environ.get(var) for var in _PROXY_ENV_VARS}
    os.environ.update(dict.fromkeys(_PROXY_ENV_VARS, proxy))
    try:
        yield
    finally:
        for var, value in saved.items():
            if value is None:
                os.environ.pop(var, None)
            else:
                os.environ[var] = value
