from typing import Any

import pytest


# Request headers and response cookies that carry credentials or session state.
# Scrubbed before a cassette is written so recordings are safe to commit and
# stay stable across re-records (auth tokens churn, identity does not).
_SENSITIVE_HEADERS = ("authorization", "cookie", "x-api-key", "x-api-token")


def _scrub_response(response: dict[str, Any]) -> dict[str, Any]:
    """Drop Set-Cookie from recorded responses; plugins never need it on replay."""
    headers = response.get("headers", {})
    for key in list(headers):
        if key.lower() == "set-cookie":
            del headers[key]
    return response


@pytest.fixture(scope="session")
def vcr_config() -> dict[str, Any]:
    """
    Shared VCR settings for the plugin replay suite.

    record_mode is left at pytest-recording's default ("none") so a cassette
    miss fails loudly instead of reaching the network. Maintainers re-record
    with `pytest --record-mode=rewrite`, which overrides this from the CLI.

    match_on includes the body because some plugins (e.g. Bunkr) POST distinct
    payloads to one API URL; without body matching every POST collapses to a
    single cassette entry.
    """
    return {
        "match_on": ["method", "scheme", "host", "port", "path", "query", "body"],
        "filter_headers": list(_SENSITIVE_HEADERS),
        "before_record_response": _scrub_response,
        # Store decoded bodies so cassettes are readable and replay does not
        # depend on the original content-encoding.
        "decode_compressed_response": True,
    }
