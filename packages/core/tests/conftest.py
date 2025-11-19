import pathlib

import pytest


HERE = pathlib.Path(__file__).parent
FIXTURES = HERE / "fixtures"


@pytest.fixture
def fixture_loader():
    """Reads a file from the fixtures directory."""

    def _load(name: str) -> str:
        path = FIXTURES / name
        if not path.exists():
            msg = f"Fixture {name} not found at {path}"
            raise FileNotFoundError(msg)
        return path.read_text(encoding="utf-8")

    return _load


def pytest_configure(config) -> None:
    config.addinivalue_line("markers", "unit: Pure logic tests (no network)")
    config.addinivalue_line("markers", "integration: Mocked network tests")
    config.addinivalue_line(
        "markers", "live: Real network tests against production sites"
    )


def pytest_collection_modifyitems(config, items) -> None:
    """Skip live tests unless --run-live is passed."""
    if config.getoption("--run-live", default=False):
        return

    skip_live = pytest.mark.skip(reason="Use --run-live to execute")
    for item in items:
        if "live" in item.keywords:
            item.add_marker(skip_live)


def pytest_addoption(parser) -> None:
    parser.addoption(
        "--run-live",
        action="store_true",
        default=False,
        help="Run tests against real sites",
    )
