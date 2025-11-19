import pathlib
import sys

import pytest


ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

HERE = pathlib.Path(__file__).parent
FIXTURES = HERE / "fixtures"


def load_fixture(name: str) -> str:
    path = FIXTURES / name
    with path.open(encoding="utf-8") as f:
        return f.read()


@pytest.fixture
def fixture_loader():
    return load_fixture


@pytest.fixture
def tmp_output_dir(tmp_path):
    d = tmp_path / "out"
    d.mkdir()
    return str(d)


def pytest_configure(config) -> None:
    config.addinivalue_line("markers", "unit: Unit tests (fast, no network)")
    config.addinivalue_line("markers", "integration: Integration tests (mocked)")
    config.addinivalue_line("markers", "live: Live tests against real sites")
    config.addinivalue_line("markers", "smoke: Quick sanity checks (always run)")
    config.addinivalue_line("markers", "auth: Tests requiring authentication")
    config.addinivalue_line("markers", "slow: Tests taking >10 seconds")
    config.addinivalue_line("markers", "downloads_file: Performs actual file downloads")


def pytest_collection_modifyitems(config, items) -> None:
    """Skip live tests unless --run-live is passed."""
    if config.getoption("--run-live", default=False):
        return

    skip_live = pytest.mark.skip(reason="use --run-live to run")
    for item in items:
        if "live" in item.keywords:
            item.add_marker(skip_live)


def pytest_addoption(parser) -> None:
    parser.addoption(
        "--run-live",
        action="store_true",
        default=False,
        help="run tests against real sites",
    )
