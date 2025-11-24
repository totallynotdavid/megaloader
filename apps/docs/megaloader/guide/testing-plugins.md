# Testing plugins

This guide covers testing strategies for megaloader plugins.

<!-- prettier-ignore -->
::: info Note
Examples in this guide reference "FileBox," a fictional platform used for
demonstration. See [Creating plugins](creating-plugins) for the implementation
walkthrough.
:::

## Testing philosophy

Live tests take priority because unit tests can’t detect API, HTML, or domain
changes on real platforms. CI runs the live suite weekly (Monday at 05:00 UTC)
to flag breakages.

Unit tests remain useful for URL parsing and edge cases, but most assurance
comes from live testing.

## Manual testing

Test manually first to verify basic functionality:

```python
from megaloader.plugins.filebox import FileBox

plugin = FileBox("https://filebox.com/album/test123")
items = list(plugin.extract())

for item in items:
    print(f"{item.filename} - {item.download_url}")
```

Test through the main interface:

```python
import megaloader as mgl

for item in mgl.extract("https://filebox.com/album/test123"):
    print(item.filename)
```

## Live tests

Add live tests in `packages/core/tests/live/test_filebox_live.py`:

```python
import pytest

from megaloader.plugins.filebox import FileBox
from tests.helpers import assert_valid_item
from tests.test_urls import FILEBOX_URLS


@pytest.mark.live
def test_filebox_album():
    url = FILEBOX_URLS["album"]

    plugin = FileBox(url)
    items = list(plugin.extract())

    assert len(items) > 0, f"No items extracted from {url}"

    for item in items:
        assert_valid_item(item)


@pytest.mark.live
def test_filebox_single_file():
    url = FILEBOX_URLS["single_file"]

    plugin = FileBox(url)
    items = list(plugin.extract())

    assert len(items) == 1, (
        f"Expected exactly 1 item from single file URL, got {len(items)}"
    )
    assert_valid_item(items[0])
```

Add test URLs to `packages/core/tests/test_urls.py`:

```python
FILEBOX_URLS = {
    "album": "https://filebox.com/album/test123",
    "single_file": "https://filebox.com/file/xyz789",
}
```

The `assert_valid_item` helper validates basic properties:

- URL starts with `http://` or `https://`
- Filename is not empty
- Filename doesn't contain path traversal (`..`) or separators (`/`)

## Unit tests

If you need unit tests for URL parsing or validation logic, add them in
`packages/core/tests/unit/test_filebox.py`:

```python
import pytest

from megaloader.plugins.filebox import FileBox


@pytest.mark.unit
def test_parse_album_url():
    plugin = FileBox("https://filebox.com/album/abc123")
    assert plugin.content_type == "album"
    assert plugin.content_id == "abc123"


@pytest.mark.unit
def test_parse_file_url():
    plugin = FileBox("https://filebox.com/file/xyz789")
    assert plugin.content_type == "file"
    assert plugin.content_id == "xyz789"


@pytest.mark.unit
def test_invalid_url():
    with pytest.raises(ValueError, match="Invalid FileBox URL"):
        FileBox("https://example.com/invalid")
```

## Running tests

Run unit tests only (takes less than 1 second):

::: code-group

```bash [pytest]
pytest packages/core/tests/unit
```

```bash [mise]
mise run test-unit
```

:::

Run all tests including live tests (takes about 100 seconds):

::: code-group

```bash [pytest]
pytest packages/core/tests --run-live
```

```bash [mise]
mise run test
```

:::

Live tests are skipped by default. Use `--run-live` to execute them.

## CI testing

The GitHub Actions workflow runs tests weekly on a schedule:

- Runs unit tests on every push/PR (commented out by default for speed)
- Runs all live tests every Monday at 05:00 UTC
- Tests run on Python 3.12 and 3.13. Testing additional versions offers little
  benefit (in my opinion) and would unnecessarily consume GitHub Actions
  minutes.
- Uploads coverage reports to Codecov. See it
  [here](https://app.codecov.io/gh/totallynotdavid/megaloader).

See `.github/workflows/test.yml` for the full configuration.

This weekly schedule catches platform changes without slowing down development.
If a live test fails, it usually means the platform changed something and the
plugin needs to be updated.
