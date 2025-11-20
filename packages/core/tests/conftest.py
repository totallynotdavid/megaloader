import pytest


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
