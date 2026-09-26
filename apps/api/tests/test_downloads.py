import io
import zipfile

from collections.abc import Callable
from pathlib import Path
from types import ModuleType

import pytest

from fastapi.testclient import TestClient
from megaloader.item import DownloadItem

from tests.conftest import DOWNLOAD_BODY
from tests.servers import Route, Server


LIMIT_MB = "0.01"
LIMIT_BYTES = int(0.01 * 1024 * 1024)

Serve = Callable[..., Server]
StubExtraction = Callable[..., None]


def download(
    load_app: Callable[..., ModuleType],
    make_client: Callable[..., TestClient],
    stub_extraction: StubExtraction,
    items: list[DownloadItem],
):
    index = load_app(API_MAX_SIZE_MB=LIMIT_MB)
    stub_extraction(index, items)
    return make_client(index).post("/download", json=DOWNLOAD_BODY)


def item(server: Server, path: str, filename: str = "file.bin") -> DownloadItem:
    return DownloadItem(download_url=server.base_url + path, filename=filename)


class TestNonPublicAddresses:
    def test_loopback_download_url_is_not_fetched(
        self, load_app, make_client, stub_extraction, serve: Serve
    ) -> None:
        internal = serve({"/secret": Route(body=b"internal")}, public=False)

        response = download(
            load_app, make_client, stub_extraction, [item(internal, "/secret")]
        )

        assert internal.hits == []
        assert response.status_code != 200
        assert b"internal" not in response.content

    def test_redirect_to_loopback_is_refused_before_it_is_fetched(
        self, load_app, make_client, stub_extraction, serve: Serve
    ) -> None:
        internal = serve({"/secret": Route(body=b"internal")}, public=False)
        public = serve(
            {
                "/file": Route(
                    status=302, headers={"Location": internal.base_url + "/secret"}
                )
            }
        )

        response = download(
            load_app, make_client, stub_extraction, [item(public, "/file")]
        )

        assert internal.hits == []
        assert response.status_code != 200
        assert b"internal" not in response.content

    def test_redirect_to_metadata_address_is_refused(
        self, load_app, make_client, stub_extraction, serve: Serve
    ) -> None:
        public = serve(
            {
                "/file": Route(
                    status=307,
                    headers={"Location": "http://169.254.169.254/latest/meta-data/"},
                )
            }
        )

        response = download(
            load_app, make_client, stub_extraction, [item(public, "/file")]
        )

        assert response.status_code != 200
        assert public.hits == ["HEAD /file", "GET /file"]

    def test_redirect_hops_are_followed_when_every_hop_is_public(
        self, load_app, make_client, stub_extraction, serve: Serve
    ) -> None:
        target = serve({"/final": Route(body=b"payload")})
        start = serve(
            {"/a": Route(status=301, headers={"Location": target.base_url + "/final"})}
        )

        response = download(load_app, make_client, stub_extraction, [item(start, "/a")])

        assert response.status_code == 200
        assert response.content == b"payload"

    def test_redirect_loop_gives_up(
        self, load_app, make_client, stub_extraction, serve: Serve
    ) -> None:
        loop = serve({})
        loop.routes["/x"] = Route(
            status=302, headers={"Location": loop.base_url + "/x"}
        )

        response = download(load_app, make_client, stub_extraction, [item(loop, "/x")])

        assert response.status_code != 200
        assert len(loop.hits) < 30

    def test_relative_redirect_is_followed(
        self, load_app, make_client, stub_extraction, serve: Serve
    ) -> None:
        host = serve(
            {
                "/a": Route(status=302, headers={"Location": "/b"}),
                "/b": Route(body=b"payload"),
            }
        )

        response = download(load_app, make_client, stub_extraction, [item(host, "/a")])

        assert response.content == b"payload"


class TestSizeLimit:
    def test_body_over_limit_without_content_length_is_413(
        self, load_app, make_client, stub_extraction, serve: Serve
    ) -> None:
        host = serve(
            {"/big": Route(body=b"x" * (LIMIT_BYTES * 3), advertise_length=False)}
        )

        response = download(
            load_app, make_client, stub_extraction, [item(host, "/big")]
        )

        assert response.status_code == 413

    def test_body_over_understated_content_length_is_413(
        self, load_app, make_client, stub_extraction, serve: Serve
    ) -> None:
        host = serve(
            {
                "/big": Route(
                    body=b"x" * (LIMIT_BYTES * 3),
                    head_length=10,
                    advertise_length=False,
                )
            }
        )

        response = download(
            load_app, make_client, stub_extraction, [item(host, "/big")]
        )

        assert response.status_code == 413

    def test_budget_is_shared_across_files(
        self, load_app, make_client, stub_extraction, serve: Serve
    ) -> None:
        body = b"x" * (LIMIT_BYTES // 2 + 100)
        host = serve(
            {
                "/1": Route(body=body, head_length=10, advertise_length=False),
                "/2": Route(body=body, head_length=10, advertise_length=False),
            }
        )

        response = download(
            load_app,
            make_client,
            stub_extraction,
            [item(host, "/1", "1.bin"), item(host, "/2", "2.bin")],
        )

        assert response.status_code == 413

    def test_partial_file_is_not_left_on_disk(
        self, load_app, make_client, stub_extraction, serve: Serve
    ) -> None:
        before = set(Path("/tmp").glob("megaloader_*"))
        host = serve(
            {"/big": Route(body=b"x" * (LIMIT_BYTES * 3), advertise_length=False)}
        )

        download(load_app, make_client, stub_extraction, [item(host, "/big")])

        assert set(Path("/tmp").glob("megaloader_*")) == before

    def test_file_exactly_at_limit_is_served(
        self, load_app, make_client, stub_extraction, serve: Serve
    ) -> None:
        host = serve({"/ok": Route(body=b"x" * LIMIT_BYTES)})

        response = download(load_app, make_client, stub_extraction, [item(host, "/ok")])

        assert response.status_code == 200
        assert len(response.content) == LIMIT_BYTES

    def test_declared_size_over_limit_returns_preview(
        self, load_app, make_client, stub_extraction, serve: Serve
    ) -> None:
        host = serve({"/big": Route(body=b"x" * (LIMIT_BYTES + 1))})

        response = download(
            load_app, make_client, stub_extraction, [item(host, "/big")]
        )

        assert response.status_code == 200
        assert response.json()["exceeds_limit"] is True

    def test_negative_content_length_counts_as_unknown(
        self, load_app, make_client, stub_extraction, serve: Serve
    ) -> None:
        host = serve({"/f": Route(body=b"data", head_length=-5)})

        response = download(load_app, make_client, stub_extraction, [item(host, "/f")])

        assert response.status_code == 200
        assert response.content == b"data"


class TestBatches:
    @pytest.mark.parametrize(
        "bad_host", ["a..b", f"{'a' * 70}.example"], ids=["empty-label", "long-label"]
    )
    def test_unresolvable_host_fails_only_its_own_file(
        self, load_app, make_client, stub_extraction, serve: Serve, bad_host: str
    ) -> None:
        host = serve({"/ok": Route(body=b"good")})
        bad = DownloadItem(download_url=f"http://{bad_host}/x", filename="bad.bin")

        response = download(
            load_app, make_client, stub_extraction, [bad, item(host, "/ok", "ok.bin")]
        )

        assert response.status_code == 200
        assert response.content == b"good"

    def test_failed_file_does_not_fail_the_batch(
        self, load_app, make_client, stub_extraction, serve: Serve
    ) -> None:
        host = serve({"/ok": Route(body=b"good")})

        response = download(
            load_app,
            make_client,
            stub_extraction,
            [item(host, "/missing", "gone.bin"), item(host, "/ok", "ok.bin")],
        )

        assert response.status_code == 200
        assert response.content == b"good"

    def test_batch_is_zipped(
        self, load_app, make_client, stub_extraction, serve: Serve
    ) -> None:
        host = serve({"/1": Route(body=b"one"), "/2": Route(body=b"two")})

        response = download(
            load_app,
            make_client,
            stub_extraction,
            [item(host, "/1", "1.bin"), item(host, "/2", "2.bin")],
        )

        names = zipfile.ZipFile(io.BytesIO(response.content)).namelist()
        assert sorted(names) == ["1.bin", "2.bin"]

    def test_all_files_failing_is_an_error(
        self, load_app, make_client, stub_extraction, serve: Serve
    ) -> None:
        host = serve({})

        response = download(
            load_app, make_client, stub_extraction, [item(host, "/missing")]
        )

        assert response.status_code == 500


class TestContentDisposition:
    @pytest.fixture
    def header(self, load_app, make_client, stub_extraction, serve: Serve):
        def fetch(filename: str) -> str:
            host = serve({"/f": Route(body=b"data")})
            response = download(
                load_app, make_client, stub_extraction, [item(host, "/f", filename)]
            )
            assert response.status_code == 200
            return response.headers["content-disposition"]

        return fetch

    def test_plain_name_has_both_forms(self, header) -> None:
        assert (
            header("report.pdf")
            == "attachment; filename=\"report.pdf\"; filename*=UTF-8''report.pdf"
        )

    def test_quotes_and_non_ascii_never_reach_the_quoted_form(self, header) -> None:
        value = header('résumé "final".txt')

        quoted = value.split("filename=", 1)[1].split(";", 1)[0]
        assert quoted.isascii()
        assert quoted.strip('"').count('"') == 0
        assert "filename*=UTF-8''r%C3%A9sum%C3%A9%20%22final%22.txt" in value

    def test_header_injection_is_neutralised(self, header) -> None:
        value = header("a.txt\r\nSet-Cookie: x=1")

        assert "\r" not in value
        assert "\n" not in value
        assert "%0D%0A" in value

    def test_name_without_ascii_falls_back(self, header) -> None:
        value = header("動画.mp4")

        assert 'filename="' in value
        assert "filename*=UTF-8''%E5%8B%95%E7%94%BB.mp4" in value
