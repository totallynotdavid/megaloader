# [pkg]: megaloader

[![CodeQL](https://github.com/totallynotdavid/megaloader/actions/workflows/codeql.yml/badge.svg)](https://github.com/totallynotdavid/megaloader/actions/workflows/codeql.yml)
[![lint and format check](https://github.com/totallynotdavid/megaloader/actions/workflows/checks.yml/badge.svg)](https://github.com/totallynotdavid/megaloader/actions/workflows/checks.yml)

This project will make you smile. Megaloader is a package written in Python that
automatically downloads content from several file hosting and media platforms.
It works with a plugin-based architecture to provide a unified interface for
downloading from multiple platforms.

> [!WARNING]
> Many supported platforms host adult content. This tool is designed
> for content creators and digital archivists who need to work with such
> platforms.

## Getting started

The package has an utomatic URL detection system makes downloading content
straightforward. The package analyzes URLs and selects the appropriate plugin
automatically (see [plugins](megaloader/plugins/__init__.py)), requiring only
the URL and destination path.

```python
from megaloader import download

download("https://pixeldrain.com/u/95u1wnsd", "./downloads")
download("https://cyberdrop.me/a/0OpiyaOV", "./downloads")
```

When you need more control over the download process, you can specify the plugin
class directly. This is useful if a platform domain changes.

```python
from megaloader import Bunkr, download

download(
    "https://bunkrr.su/d/megaloader-main-RKEICuly.zip",
    "./downloads",
    plugin_class=Bunkr,
)
```

The downloaded files are organized in the specified directory, with plugins
automatically creating subdirectories based on album names or content structure
when appropriate.

## Supported platforms

We currently support 11 platforms with different maintenance priorities. Core
platforms receive active development and feature updates, while extended
platforms are maintained on a best-effort basis.

| Platform    | Domain(s)                                        | Features                             | Priority |
| ----------- | ------------------------------------------------ | ------------------------------------ | -------- |
| Bunkr       | bunkr.si, bunkr.la, bunkr.is, bunkr.ru, bunkr.su | Albums, single files, API extraction | Core     |
| PixelDrain  | pixeldrain.com                                   | Files, lists, proxy support          | Core     |
| Cyberdrop   | cyberdrop.me, cyberdrop.to                       | Albums, galleries                    | Core     |
| GoFile      | gofile.io                                        | Password-protected folders           | Core     |
| Fanbox      | {creator}.fanbox.cc, fanbox.cc/@{creator}        | Creator content, authentication      | Extended |
| Pixiv       | pixiv.net                                        | Artwork, user galleries              | Extended |
| Rule34      | rule34.xxx                                       | Search results, posts                | Extended |
| ThotsLife   | thotslife.com                                    | Albums, profiles                     | Extended |
| ThotHub.VIP | thothub.vip                                      | Platform content                     | Extended |
| ThotHub.TO  | thothub.to                                       | Platform content                     | Extended |
| Fapello     | fapello.com                                      | Profile extraction                   | Extended |

> [!NOTE]
> Extended plugins work as of 2025/08/25 but may occasionally break
> without immediate fixes since I don't really use them.

## Installation

Python 3.10 or newer is required, though we recommend Python 3.13 or higher for
reproducibility. The installation process varies depending on your preferred
dependency management approach.

Begin by cloning the repository to your local machine:

```bash
git clone https://github.com/totallynotdavid/megaloader
cd megaloader
```

<details>
<summary>
#### Standard pip installation
</summary>

For users familiar with traditional Python package management, install
dependencies directly from the requirements file. This method works across all
Python environments and doesn't require additional tooling.

On macOS/Linux:

```bash
python3 -m pip install -r requirements.txt
```

On Windows:

```bash
python -m pip install -r requirements.txt
```

</details>

<details>
<summary>
#### Poetry installation
</summary>

After installing Poetry following their
[official guide](https://python-poetry.org/docs/#installing-with-the-official-installer),
install the project dependencies:

```bash
poetry install
```

</details>

<details>
<summary>
#### UV installation
</summary>

uv offers faster dependency resolution and installation than pip. After
[installing uv](https://docs.astral.sh/uv/getting-started/installation/), set up
the project:

```bash
uv install
```

</details>

<details>
<summary>

#### Recommended: mise installation

</summary>

I recommend mise for the most reliable setup experience across different
operating systems. Mise automatically manages Python versions, tool
installations, and project tasks. After
[installing mise](https://mise.jdx.dev/getting-started.html):

```bash
mise install      # Sets up Python 3.13.7, uv, and ruff automatically
mise run install  # Installs project dependencies
```

</details>

### Testing the installation

Once installation is complete, verify everything works by running the example
script. This script demonstrates basic functionality and helps confirm your
setup:

If you're using mise/uv:

```bash
uv run example.py
```

If you're using standard Python:

```bash
python example.py
```

The example script located at [example.py](example.py) contains usage examples
that showcase the package's core features.

## Project background

This project was originally created by [@Ximaz](https://github.com/Ximaz), but
the original repository was deleted or made private sometime during or
after 2023. I've taken over development and completely refactored the codebase
to fix issues caused by changes made by the supported sites.

The
[original implementation](https://github.com/totallynotdavid/megaloader/tree/9adeffe2d4055d26f9db2b7fcbf6f92de0aca628)
served as inspiration, but the current codebase has been mostly rebuilt from the
ground up. Development priorities focus on four core platforms (Bunkr,
PixelDrain, Cyberdrop, and GoFile) while maintaining best-effort support for
extended platforms.

> [!TIP]
> Report issues through the
> [GitHub Issues](https://github.com/totallynotdavid/megaloader/issues) tracker.
> Include specific URLs, complete error messages with DEBUG logging enabled, and
> your Python version.

## Architecture overview

The project uses a plugin-based architecture where each supported platform is
implemented as a separate plugin inheriting from the `BasePlugin` abstract base
class defined in [megaloader/plugin.py](megaloader/plugin.py).

Each plugin implements two core methods that handle the complete download
workflow:

- The `export()` method parses platform-specific pages and extracts file
  information, yielding `Item` objects containing download metadata.
- The `download_file()` method handles actual file retrieval and storage,
  returning success or failure status.

The `Item` dataclass serves as the communication bridge between extraction and
download operations:

```python
@dataclass
class Item:
    url: str                                   # Direct download URL
    filename: str                              # Suggested filename
    album_title: Optional[str] = None          # Album/collection name
    file_id: Optional[str] = None              # Platform-specific ID
    metadata: Optional[dict[str, Any]] = None  # Additional platform data
```

## Advanced usage

Several plugins support additional configuration options that enable specialized
functionality. These options are passed as keyword arguments to the `download()`
function or plugin constructor.

### PixelDrain proxy support

PixelDrain includes an optional proxy system that can help bypass rate limiting.
This feature uses proxies provided by [@sh13y](https://github.com/sh13y) via
[Cloudflare workers](https://github.sh13y/pixeldrain-ratelimit-bypasser). The
proxy option is disabled by default since it requires trusting external
infrastructure. You can use it like this:

```python
download(
    "https://pixeldrain.com/l/nH4ZKt3b",
    "./downloads",
    use_proxy=True
)
```

### GoFile password support

GoFile allows uploaders to password-protect their albums and folders. The plugin
supports this authentication mechanism through the password parameter.

```python
download(
    "https://gofile.io/d/protected_folder",
    "./downloads",
    password="secret123"
)
```

### Direct plugin usage

For applications requiring fine-grained control over the download process, you
can import and use plugin classes directly.

```python
from megaloader.plugins import Cyberdrop

plugin = Cyberdrop("https://cyberdrop.me/a/album_id")

# Extract all items first for progress tracking
items = list(plugin.export())
print(f"Found {len(items)} files to download")

# Download with custom logic
for i, item in enumerate(items):
    print(f"Downloading {i+1}/{len(items)}: {item.filename}")
    success = plugin.download_file(item, "./downloads/")
    if not success:
        print(f"Failed to download {item.filename}")
```

## Contributing

We welcome contributions ranging from bug fixes to new platform support. The
development workflow emphasizes code quality through automated tooling and
comprehensive type checking.

The project includes several automated tasks that maintain code quality and
consistency. These tools are configured in [pyproject.toml](pyproject.toml)
([ruff](pyproject.toml?plain=1#L32) and [mypy](pyproject.toml?plain=1#L69)) and
can be executed through mise:

```bash
mise run fix     # Format code and apply automated fixes via ruff
mise run mypy    # Run comprehensive type checking
mise run export  # Update requirements.txt from pyproject.toml
```

All contributions must pass the automated CI pipeline, which includes type
safety verification, code style enforcement, and security scanning through
CodeQL. Running `mise run mypy` and `mise run fix` locally ensures your changes
will partially pass the automated checks.

### Creating new plugins

New platform plugins should follow established patterns for consistency and
maintainability. The basic structure requires inheriting from `BasePlugin` and
implementing the two core methods, with registration in the domain registry for
automatic URL detection.

```python
class NewPlatformPlugin(BasePlugin):
    def __init__(self, url: str, **kwargs: Any) -> None:
        super().__init__(url, **kwargs)
        # Initialize HTTP session, configure headers, handle authentication

    def export(self) -> Generator[Item, None, None]:
        # Parse platform URLs and extract file information
        # Handle pagination, albums, and individual files
        # Yield Item objects with complete download metadata
        pass

    def download_file(self, item: Item, output_dir: str) -> bool:
        # Execute actual file download and storage
        # Handle platform-specific download logic
        # Return success/failure status for error handling
        return True
```

Register your plugin in the domain mapping located in
[megaloader/plugins/**init**.py](megaloader/plugins/__init__.py) to enable
automatic URL detection.

### Technical details

The runtime maintains a minimal dependency footprint with three core libraries.
`requests` handles HTTP operations and session management, `beautifulsoup4`
provides HTML parsing capabilities, and `lxml` serves as the high-performance
parser backend. Development dependencies include `ruff` for code formatting and
linting, plus `mypy` for static type checking. The complete dependency tree is
available in [requirements.txt](requirements.txt).

Configuration management centralizes around [pyproject.toml](pyproject.toml),
which contains settings for all tools including ruff, mypy, and packaging
metadata. The [mise.toml](mise.toml) file provides development environment
automation with exact tool versions and task orchestration for consistent
development experiences.

## Getting help

For **bug reports** use
[GitHub Issues](https://github.com/totallynotdavid/megaloader/issues). Make sure
to include your Python version, complete error messages, stack traces, and
problematic URLs. Include DEBUG-level logging output to speed up debugging.

For **feature requests**, submit through GitHub Issues with their respective use
cases, supported platforms, example URLs, and workflow explanations.

For **general questions**, use GitHub Discussions for questions about usage,
architecture, or integration. This helps build a knowledge base for the
community.
