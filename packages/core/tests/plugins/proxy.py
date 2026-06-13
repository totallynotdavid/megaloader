"""Geonode rotating-proxy wiring shared by the recording fixture and the probe.

Both the autouse recording fixture (`conftest._rotating_proxy`) and the manual
probe CLI (`probe.py`) build proxy URLs the same way: one random port from the
configured range per call, so consecutive requests spread across exit IPs to
dodge per-IP rate limits. Credentials come from the environment first, then a
flat `.env` at the repo root.
"""

import os
import random

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[4]
ENV_PATH = PROJECT_ROOT / ".env"

REQUIRED_CREDS = (
    "GEONODE_USERNAME",
    "GEONODE_PASSWORD",
    "GEONODE_HOST",
    "GEONODE_PORT_RANGE",
)


def load_env_file(path: Path = ENV_PATH) -> dict[str, str]:
    """Parse a flat KEY=VALUE .env file, ignoring comments and blank lines.

    Proxy creds contain no '=' or whitespace, so a straight partition is enough.
    """
    if not path.is_file():
        return {}

    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        values[key.strip()] = value.strip()
    return values


def credentials() -> dict[str, str]:
    """Real environment overlaid on the .env file (environment wins)."""
    return {**load_env_file(), **os.environ}


def missing_creds(creds: dict[str, str]) -> list[str]:
    return [key for key in REQUIRED_CREDS if not creds.get(key)]


def proxy_url(creds: dict[str, str] | None = None) -> str:
    """Build an http://user:pass@host:port URL with one port from the range."""
    creds = creds or credentials()
    start_str, _, end_str = creds["GEONODE_PORT_RANGE"].partition("-")
    start, end = int(start_str), int(end_str)
    if end < start:
        msg = f"GEONODE_PORT_RANGE end < start: {creds['GEONODE_PORT_RANGE']}"
        raise ValueError(msg)
    port = random.randint(start, end)
    user, password, host = (
        creds["GEONODE_USERNAME"],
        creds["GEONODE_PASSWORD"],
        creds["GEONODE_HOST"],
    )
    return f"http://{user}:{password}@{host}:{port}"
