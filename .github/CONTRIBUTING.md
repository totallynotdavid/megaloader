# Contributing

## Setup

Clone the repository and install dependencies. The project uses uv for
dependency management:

```bash
git clone https://github.com/totallynotdavid/megaloader
cd megaloader
uv sync
```

Python 3.13+ is recommended for reproducibility. The project includes mise
configuration for automated tool setup. If you prefer automated environment
management, run:

```bash
mise install
mise run install
```

## Testing

Run the full test suite including live API tests:

```bash
uv run pytest
```

Run unit tests only to skip slow integration tests:

```bash
uv run pytest -m "not integration"
```

Format the code and run type checks before committing:

```bash
uv run ruff format .
uv run ruff check --fix .
uv run mypy packages/core
```

If you have mise installed, you can instead run:

```bash
mise run format
mise run mypy
mise run test
```

## Creating plugins

Plugins inherit from `BasePlugin` and implement the `extract()` method. This
method yields `DownloadItem` objects containing file metadata:

```python
from megaloader.plugin import BasePlugin
from megaloader.item import DownloadItem
from collections.abc import Generator
from typing import Any

class NewPlatformPlugin(BasePlugin):
    def __init__(self, url: str, **kwargs: Any) -> None:
        super().__init__(url, **kwargs)
        self.session.headers.update({"User-Agent": "..."})

    def extract(self) -> Generator[DownloadItem, None, None]:
        response = self.session.get(self.url)
        response.raise_for_status()

        # Parse response and extract file information
        yield DownloadItem(
            filename="example.jpg",
            download_url="https://...",
            size_bytes=1024,
        )
```

Register your plugin in `packages/core/megaloader/plugins/__init__.py` by adding
a domain mapping to `PLUGIN_REGISTRY`:

```python
PLUGIN_REGISTRY: dict[str, type[BasePlugin]] = {
    "newplatform.com": NewPlatformPlugin,
}
```

For subdomain support like `creator.fanbox.cc`, add the base domain to
`SUBDOMAIN_SUPPORTED_DOMAINS`.

Handle network errors broadly. Individual failures should be logged without
stopping the entire extraction:

```python
try:
    response = self.session.get(url)
    response.raise_for_status()
except requests.RequestException as e:
    logger.warning(f"Failed to fetch {url}: {e}")
    return
```

## Dependencies

Keep runtime dependencies minimal. The core library depends on requests,
beautifulsoup4, and lxml. Avoid adding additional dependencies unless necessary.

Development dependencies include ruff for formatting, mypy for type checking,
and pytest for testing. Their configurations are set in the root pyproject.toml.

## Submitting changes

Create a feature branch from main. Keep pull requests focused on a single
feature or fix. Run format and type checks before committing. Test thoroughly,
especially for new plugins.

Write clear commit messages and PR descriptions. Explain what problem you're
solving and how. Update documentation for public API changes.

Use GitHub Discussions for design questions before starting large changes. When
reporting bugs, include your Python version, error messages, and relevant URLs.
