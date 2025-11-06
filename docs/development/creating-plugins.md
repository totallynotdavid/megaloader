# Creating Custom Plugins

Learn how to create your own plugins to support additional platforms.

## Plugin Architecture

A Megaloader plugin is a Python class that:

1. Extends `BasePlugin`
2. Implements `export()` to extract downloadable items
3. Implements `download_file()` to download individual items

## Basic Plugin Template

```python
from megaloader.plugin import BasePlugin, Item
from typing import Generator
import requests
from bs4 import BeautifulSoup

class MyPlugin(BasePlugin):
    """Plugin for downloading from example.com."""

    def export(self) -> Generator[Item, None, None]:
        """
        Extract downloadable items from the URL.

        Yields:
            Item: Each downloadable file found at the URL
        """
        # Parse the URL to get the content ID
        content_id = self._parse_url()

        # Fetch the page
        response = requests.get(f"https://example.com/content/{content_id}")
        response.raise_for_status()

        # Parse HTML to find download links
        soup = BeautifulSoup(response.text, 'html.parser')

        for link in soup.find_all('a', class_='download-link'):
            file_url = link['href']
            filename = link.text.strip()

            yield Item(
                url=file_url,
                filename=filename,
                album_title="My Album",  # Optional
                file_id=content_id,      # Optional
                metadata={"source": "example.com"}  # Optional
            )

    def download_file(self, item: Item, output_dir: str) -> bool:
        """
        Download a single item to the specified directory.

        Args:
            item: The item to download (from export())
            output_dir: Directory to save the file to

        Returns:
            bool: True if download succeeded, False otherwise
        """
        try:
            # Download the file
            response = requests.get(item.url, stream=True)
            response.raise_for_status()

            # Save to file
            output_path = Path(output_dir) / item.filename
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            return True
        except Exception as e:
            print(f"Error downloading {item.filename}: {e}")
            return False

    def _parse_url(self) -> str:
        """Extract content ID from URL."""
        # Example: https://example.com/content/abc123
        parts = self.url.split('/')
        return parts[-1]
```

## Step-by-Step Guide

### 1. Create Plugin File

Create a new file in `packages/core/megaloader/plugins/`:

```bash
touch packages/core/megaloader/plugins/mysite.py
```

### 2. Implement BasePlugin

```python
from megaloader.plugin import BasePlugin, Item
from typing import Generator
import requests

class MySite(BasePlugin):
    """Download files from mysite.com."""

    def __init__(self, url: str, **kwargs):
        super().__init__(url, **kwargs)
        # Custom initialization if needed
        self.session = requests.Session()
```

### 3. Implement export()

Extract all downloadable items:

```python
def export(self) -> Generator[Item, None, None]:
    """Extract items from the page."""
    # Fetch and parse the page
    response = self.session.get(self.url)
    data = response.json()  # or use BeautifulSoup for HTML

    # Extract items
    for file_data in data['files']:
        yield Item(
            url=file_data['download_url'],
            filename=file_data['name'],
            album_title=data.get('album_name'),
            file_id=file_data['id'],
        )
```

### 4. Implement download_file()

Download individual items:

```python
from pathlib import Path

def download_file(self, item: Item, output_dir: str) -> bool:
    """Download a single file."""
    try:
        output_path = Path(output_dir) / item.filename
        output_path.parent.mkdir(parents=True, exist_ok=True)

        response = self.session.get(item.url, stream=True)
        response.raise_for_status()

        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        return True
    except Exception:
        return False
```

### 5. Register Plugin

Add your plugin to `packages/core/megaloader/plugins/__init__.py`:

```python
from megaloader.plugins.mysite import MySite

# Add to __all__
__all__ = [
    # ... existing plugins
    "MySite",
]

# Add to PLUGIN_REGISTRY
PLUGIN_REGISTRY: dict[str | tuple[str, ...], type[BasePlugin]] = {
    # ... existing plugins
    "mysite.com": MySite,
}
```

### 6. Add Tests

Create test file `packages/core/tests/unit/test_mysite.py`:

```python
import pytest
from megaloader.plugins import MySite

def test_mysite_initialization():
    """Test MySite plugin initializes correctly."""
    plugin = MySite("https://mysite.com/file/123")
    assert plugin.url == "https://mysite.com/file/123"

def test_mysite_export(requests_mock):
    """Test MySite extracts items correctly."""
    # Mock the API response
    requests_mock.get(
        "https://mysite.com/file/123",
        json={"files": [{"download_url": "http://...", "name": "file.jpg"}]}
    )

    plugin = MySite("https://mysite.com/file/123")
    items = list(plugin.export())

    assert len(items) == 1
    assert items[0].filename == "file.jpg"
```

## Advanced Features

### Authentication

Handle authentication in `__init__`:

```python
def __init__(self, url: str, **kwargs):
    super().__init__(url, **kwargs)

    # Get token from environment
    token = os.getenv("MYSITE_TOKEN")
    if not token:
        raise ValueError("MYSITE_TOKEN environment variable required")

    self.session = requests.Session()
    self.session.headers['Authorization'] = f'Bearer {token}'
```

### Pagination

Handle paginated results:

```python
def export(self) -> Generator[Item, None, None]:
    """Export with pagination support."""
    page = 1

    while True:
        response = self.session.get(f"{self.url}?page={page}")
        data = response.json()

        for file_data in data['files']:
            yield Item(...)

        if not data.get('has_next_page'):
            break

        page += 1
```

### Error Handling

Robust error handling:

```python
import logging

logger = logging.getLogger(__name__)

def export(self) -> Generator[Item, None, None]:
    """Export with error handling."""
    try:
        response = self.session.get(self.url)
        response.raise_for_status()
    except requests.HTTPError as e:
        logger.error(f"HTTP error: {e}")
        return
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return

    # Process items...
```

### Rate Limiting

Respect rate limits:

```python
import time

def download_file(self, item: Item, output_dir: str) -> bool:
    """Download with rate limiting."""
    # Wait between downloads
    time.sleep(1)

    # ... download logic
```

## Best Practices

### 1. Type Hints

Always use type hints:

```python
from typing import Generator
from megaloader.plugin import Item

def export(self) -> Generator[Item, None, None]:
    ...

def download_file(self, item: Item, output_dir: str) -> bool:
    ...
```

### 2. Error Messages

Provide helpful error messages:

```python
if not self.url.startswith('https://mysite.com'):
    raise ValueError(
        "Invalid URL. Expected format: https://mysite.com/content/ID"
    )
```

### 3. Documentation

Document your plugin:

```python
class MySite(BasePlugin):
    """
    Plugin for downloading from mysite.com.

    Supports:
        - Single files
        - Collections/albums
        - Password-protected content

    Environment Variables:
        MYSITE_TOKEN: Authentication token (required)

    Example:
        >>> plugin = MySite("https://mysite.com/file/123")
        >>> items = list(plugin.export())
    """
```

### 4. Logging

Use logging instead of print:

```python
import logging

logger = logging.getLogger(__name__)

def export(self) -> Generator[Item, None, None]:
    logger.debug(f"Fetching content from {self.url}")
    # ...
```

## Testing Your Plugin

### Manual Testing

```python
from megaloader.plugins import MySite

# Test initialization
plugin = MySite("https://mysite.com/content/123")

# Test export
items = list(plugin.export())
print(f"Found {len(items)} items")

# Test download
for item in items:
    success = plugin.download_file(item, "./test-downloads")
    print(f"{item.filename}: {'✓' if success else '✗'}")
```

### Integration Testing

Create integration test:

```python
# tests/integration/test_mysite_integration.py

import pytest
from megaloader.plugins import MySite

@pytest.mark.live
def test_mysite_real_download():
    """Test actual download from mysite.com."""
    plugin = MySite("https://mysite.com/test-content")
    items = list(plugin.export())

    assert len(items) > 0

    # Test downloading first item
    success = plugin.download_file(items[0], "./test-downloads")
    assert success
```

## Submitting Your Plugin

1. Ensure tests pass
2. Update documentation
3. Create pull request
4. Follow [Contributing Guide](contributing.md)

## Examples

See existing plugins for reference:

- `bunkr.py` - Basic album support
- `pixeldrain.py` - Proxy support
- `gofile.py` - Password-protected content
- `pixiv.py` - Authentication

## See Also

- [Plugin System Guide](../guide/plugins.md)
- [Plugins API Reference](../api/plugins.md)
- [Contributing Guide](contributing.md)
