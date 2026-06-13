# Testing plugins

This guide covers testing strategies for megaloader plugins.

<!-- prettier-ignore -->
::: info Note
Examples in this guide reference "FileBox," a fictional platform used for
demonstration. See [Creating plugins](creating-plugins) for the implementation
walkthrough.
:::

## Testing philosophy

Two surfaces, each with one job:

- **Unit tests** (`tests/unit/`) cover pure logic: URL routing, parsing, crypto,
  and error handling. Hand-written inputs are fine here because the input's
  shape is the thing under test.
- **Plugin tests** (`tests/plugins/`) replay a recorded HTTP cassette through
  the real plugin and snapshot the result. They prove the full traversal works
  against responses the site actually returned, with no network on a normal run.

The same plugin test doubles as the live check: `--record-mode=rewrite`
re-fetches from the live site through the proxy, so refreshing a cassette and
detecting "the platform changed" are the same action. A cassette is real
network truth with an expiry date; the scheduled drift run renews it.

## Manual testing

Test through the public interface first to verify basic functionality:

```python
import megaloader as mgl

for item in mgl.extract("https://filebox.com/album/test123"):
    print(f"{item.filename} - {item.download_url}")
```

`extract()` owns the network. A plugin never does I/O itself: it receives a
`fetch` callable and describes requests as data, which is what makes the offline
tests below possible.

## Plugin tests

Add a module in `packages/core/tests/plugins/test_filebox.py`. Each test drives
the public `extract()`, asserts the items are valid, and snapshots the
normalized result:

```python
import pytest

from megaloader import extract
from syrupy.assertion import SnapshotAssertion

from tests.helpers import assert_valid_item
from tests.plugins.normalize import normalize_items
from tests.test_urls import FILEBOX_URLS


@pytest.mark.vcr
def test_filebox_album(snapshot: SnapshotAssertion) -> None:
    items = list(extract(FILEBOX_URLS["album"]))

    assert items
    for item in items:
        assert_valid_item(item)
    assert normalize_items(items) == snapshot


@pytest.mark.vcr
def test_filebox_single_file(snapshot: SnapshotAssertion) -> None:
    items = list(extract(FILEBOX_URLS["single_file"]))

    assert len(items) == 1
    assert_valid_item(items[0])
    assert normalize_items(items) == snapshot
```

Add the fixture URLs to `packages/core/tests/test_urls.py`:

```python
FILEBOX_URLS = {
    "album": "https://filebox.com/album/test123",
    "single_file": "https://filebox.com/file/xyz789",
}
```

Then record once and verify the replay passes offline:

```bash
uv run pytest tests/plugins/test_filebox.py --record-mode=rewrite --snapshot-update
uv run pytest tests/plugins/test_filebox.py --block-network
```

Recording needs proxy credentials (`GEONODE_*` in the project-root `.env`); the
suite fails fast without them rather than reaching bare egress. Auth plugins also
need their session secret exported. Cookies and tokens are scrubbed before a
cassette is written, so recordings are safe to commit. Prefer small fixtures: a
model that walks hundreds of detail pages makes a huge, brittle cassette. Cover
that pagination with a `fake_fetcher` unit test and point the cassette at a
single item instead. See `packages/core/tests/plugins/readme.md` for the full
recording workflow.

`assert_valid_item` checks the basics: an `http(s)` URL, a non-empty filename,
and no path traversal (`..`) or separators (`/`).

## Unit tests

Routing and parsing are pure functions, so test them directly in
`packages/core/tests/unit/`:

```python
import pytest

from megaloader.plugins.filebox import Album, File, parse_target


@pytest.mark.unit
def test_parse_album_url() -> None:
    assert parse_target("https://filebox.com/album/abc123") == Album("abc123")


@pytest.mark.unit
def test_parse_file_url() -> None:
    assert parse_target("https://filebox.com/file/xyz789") == File("xyz789")


@pytest.mark.unit
def test_invalid_url() -> None:
    assert parse_target("https://filebox.com/invalid") is None
```

To exercise error handling or traversal boundaries that a cassette can't capture
(a 404 that ends pagination, a malformed payload), drive the plugin with
`fake_fetcher`, mapping each URL to a canned body or an injected exception:

```python
from tests.helpers import fake_fetcher

routes = {"https://filebox.com/album/abc123": "<html>...</html>"}
items = list(FileBox("https://filebox.com/album/abc123").extract(fake_fetcher(routes)))
```

## Running tests

Run the full offline suite (unit + replay, no network):

::: code-group

```bash [pytest]
pytest --block-network packages/core/tests
```

```bash [mise]
mise run test
```

:::

Run unit tests only:

::: code-group

```bash [pytest]
pytest packages/core/tests/unit
```

```bash [mise]
mise run test-unit
```

:::

Re-fetch every fixture through the proxy and refresh cassettes + snapshots:

::: code-group

```bash [pytest]
uv run --env-file .env pytest packages/core/tests/plugins \
  --record-mode=rewrite --snapshot-update
```

```bash [mise]
mise run test-record
```

:::

## CI testing

Two workflows:

- `test.yml` runs the offline suite (unit + cassette replay, `--block-network`)
  on every push and PR, on Python 3.12 and 3.13, and uploads coverage to
  [Codecov](https://app.codecov.io/gh/totallynotdavid/megaloader).
- `live.yml` runs weekly (Monday 05:00 UTC). It re-fetches every fixture through
  the proxy and compares against the committed snapshots without updating them,
  so a mismatch surfaces as drift. It is allowed to fail without blocking anyone.

When the drift check fails, the platform usually changed something: re-record the
affected cassettes locally and review the snapshot diff to see what moved.
