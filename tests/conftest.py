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
    with open(path, encoding="utf-8") as f:
        return f.read()


@pytest.fixture
def fixture_loader():
    return load_fixture


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "live: mark test as requiring live network access"
    )


@pytest.fixture
def tmp_output_dir(tmp_path):
    d = tmp_path / "out"
    d.mkdir()
    return str(d)
