# Testing plugins

Plugin tests live in `packages/core/tests/`. Two kinds cover a plugin, and each
has one job.

| Directory                      | Tests                                                           | Input                                   |
| ------------------------------ | --------------------------------------------------------------- | --------------------------------------- |
| `packages/core/tests/unit/`    | Parsing, URL classification, and error handling                 | Hand-written strings and `fake_fetcher` |
| `packages/core/tests/plugins/` | Full traversal and item assembly through the public `extract()` | Recorded responses (vcr cassettes)      |

A test in `packages/core/tests/plugins/` replays a real recording, so it asserts
what the site returns and not what a developer imagined it returns. Hand-written
input belongs in `packages/core/tests/unit/`, where the input's shape is the
thing under test.

Run the offline suite:

```bash
mise run test
```

It is `pytest --block-network packages/core/tests`. It needs no network and no
credentials.

## Unit tests with `fake_fetcher`

`fake_fetcher` in `packages/core/tests/helpers.py` builds a `Fetcher` from a
dictionary of request URL to outcome. A `str` becomes a `200` response with that
body. A `Response` is returned as is. An exception is raised. A URL missing from
the dictionary fails the test, so a plugin cannot reach the network by accident.

```python
import pytest

from megaloader.plugins.thotslife import Thotslife

from tests.helpers import fake_fetcher


@pytest.mark.unit
def test_post_lists_videos_and_images() -> None:
    url = "https://thotslife.com/some-post/"
    page = (
        '<h1 class="entry-title">Set</h1>'
        '<div itemprop="articleBody">'
        '<video><source src="https://cdn.example/a.mp4"></video>'
        '<img data-src="https://cdn.example/b.jpg">'
        "</div>"
    )

    items = list(Thotslife(url).extract(fake_fetcher({url: page})))

    assert [item.filename for item in items] == ["a.mp4", "b.jpg"]
    assert items[0].collection_name == "Set"
```

Use this style for pagination boundaries and failures that a recording cannot
capture cleanly. `test_model_traversal_stops_on_404` in
`packages/core/tests/unit/test_faults.py` injects an `ExtractionError` with
`http_status=404` to end a model listing.

## Recorded tests

One module per plugin, named `packages/core/tests/plugins/test_<plugin>.py`.
Each test is marked `@pytest.mark.vcr`, calls `extract()` on a fixture URL,
validates each item, and compares the normalised items with a snapshot:

```python
@pytest.mark.vcr
def test_pixeldrain_list_images(snapshot: SnapshotAssertion) -> None:
    items = list(extract(PIXELDRAIN_URLS["images"]))

    assert items
    for item in items:
        assert_valid_item(item)
    assert normalize_items(items) == snapshot
```

| Path                                                           | Holds                                                                                                           |
| -------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| `packages/core/tests/test_urls.py`                             | The fixture URLs, one dictionary per platform.                                                                  |
| `packages/core/tests/plugins/cassettes/test_<plugin>/*.yaml`   | The recorded HTTP exchanges.                                                                                    |
| `packages/core/tests/plugins/__snapshots__/test_<plugin>.ambr` | The syrupy snapshot of the extracted items.                                                                     |
| `packages/core/tests/plugins/normalize.py`                     | `normalize_items`, which drops each download URL's query string, so signed CDN parameters do not read as drift. |
| `packages/core/tests/helpers.py`                               | `assert_valid_item`, which rejects a non-HTTP URL and an unsafe filename.                                       |

Vcr matches a request on method, scheme, host, port, path, query, and body. It
removes the `Authorization`, `Cookie`, `X-Api-Key`, and `X-Api-Token` request
headers, and `Set-Cookie` from responses, before it writes a cassette
(`packages/core/tests/conftest.py`). A request that a cassette lacks fails the
test.

Prefer a small album or a single file as the fixture. A model that walks
hundreds of pages makes a large, brittle cassette. Cover its pagination with a
`fake_fetcher` test.

## Record a cassette

Recording sends real requests, so it goes through a rotating Geonode proxy that
gives each test its own exit IP. Put these values in the environment or in
`.env` at the repository root:

```bash
GEONODE_USERNAME=...
GEONODE_PASSWORD=...
GEONODE_HOST=...
GEONODE_PORT_RANGE=10000-10100
```

A recording run fails when one is missing. Replay never reads them.

Record every plugin and update the snapshots:

```bash
mise run test-record
```

Record one plugin. Plugins that need a credential also read it from the
environment:

```bash
PIXIV_PHPSESSID=... uv run --all-packages --extra dev pytest \
  packages/core/tests/plugins/test_pixiv.py --record-mode=rewrite --snapshot-update
```

Then run `mise run test` to confirm the new cassette replays offline, and commit
the cassettes and the `.ambr` files together. The snapshot diff shows what
changed on the site.

`mise run proxy-probe -- <url>` sends one request through the same proxy for
debugging a live site. It accepts `-X`, headers, cookies, and `--no-proxy`.

## Add tests for a new plugin

1. Add fixture URLs to `packages/core/tests/test_urls.py`.
2. Create `packages/core/tests/plugins/test_<plugin>.py` in the shape above.
3. Record it with `--record-mode=rewrite --snapshot-update`, and run
   `mise run test`.
4. Add unit tests for URL classification, parsing helpers, and failure paths.

## Continuous integration

| Workflow   | Runs                                                                                                                    |
| ---------- | ----------------------------------------------------------------------------------------------------------------------- |
| `test.yml` | The offline suite with `--block-network` on Python 3.10, 3.12, 3.13, and 3.14.                                          |
| `live.yml` | A weekly run that re-records the plugin cassettes against the live sites. A snapshot mismatch means a platform changed. |
