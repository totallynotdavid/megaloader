from collections.abc import Callable
from types import ModuleType

import pytest

from fastapi.testclient import TestClient
from megaloader.exceptions import ExtractionError

from tests.conftest import DOWNLOAD_BODY


@pytest.mark.parametrize(
    ("category", "status"),
    [
        ("rate_limit", 429),
        ("auth", 401),
        ("access", 404),
        ("network", 502),
        ("timeout", 504),
        ("protocol", 502),
        ("unknown", 500),
        ("something_new", 500),
    ],
)
def test_extraction_category_maps_to_status(
    load_app: Callable[..., ModuleType],
    make_client: Callable[..., TestClient],
    monkeypatch: pytest.MonkeyPatch,
    category: str,
    status: int,
) -> None:
    index = load_app()

    def fail(url: str, domain: str) -> None:
        raise ExtractionError("boom", category=category)

    monkeypatch.setattr(index, "extract_items", fail)

    response = make_client(index).post("/download", json=DOWNLOAD_BODY)

    assert response.status_code == status
    assert "boom" not in response.text
