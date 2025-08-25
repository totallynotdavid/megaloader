# [pkg]: megaloader

[![CodeQL](https://github.com/totallynotdavid/megaloader/actions/workflows/codeql.yml/badge.svg)](https://github.com/totallynotdavid/megaloader/actions/workflows/codeql.yml)
[![lint and format check](https://github.com/totallynotdavid/megaloader/actions/workflows/checks.yml/badge.svg)](https://github.com/totallynotdavid/megaloader/actions/workflows/checks.yml)

This project will make you smile. Megaloader is a package written in Python to
automate downloads from various file hosting and media platforms.

> [!WARNING]
> Many supported platforms host adult content. This tool is designed
> for content creators and digital archivists who need to work with such
> platforms.

## Quick start

The simplest way to use Megaloader is through its automatic URL detection
system:

```python
from megaloader import download

download("https://pixeldrain.com/u/95u1wnsd", "./downloads")
download("https://cyberdrop.me/a/0OpiyaOV", "./downloads")
```

You only need to pass the URL and the path to the folder where you want to store
the downloaded files. For more control, you can work with plugins directly:

```python
from megaloader import Bunkr, download

download(
    "https://bunkrr.su/d/megaloader-main-RKEICuly.zip",
    "./downloads",
    plugin_class=Bunkr,
)
```

In both cases, the files will be stored in the specified download directory.

## Supported platforms

Currently, Megaloader supports 11 different platforms with varying levels of
maintenance priority:

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
> **Core** plugins receive active maintenance and feature development.
> **Extended** plugins are supported on a best-effort basis and may occasionally
> break without immediate fixes as I don't personally use them. They all work as
> of 2025/08/25

## Installation

You need a modern Python version, I tried to give support to at least Python
3.10, but I recommend using Python 3.13 or higher (see [mise.toml](mise.toml)),
however, older versions may work without issues.

We'll walk through several installation methods to match your development
workflow.

First, clone the repository to your local machine:

```bash
git clone https://github.com/totallynotdavid/megaloader
cd megaloader
```

Pick your poison:

<details>
<summary>**For most users (standard pip)**</summary>

If you're familiar with traditional Python package management, install
dependencies from our requirements file:

```bash
# On macOS/Linux
python3 -m pip install -r requirements.txt

# On Windows
python -m pip install -r requirements.txt
```

</details>

Or if you're a developer:

<details>
<summary>**For [Poetry](https://python-poetry.org/docs/#installing-with-the-official-installer) users**</summary>

If your workflow already includes Poetry for dependency management:

```bash
poetry install
```

</details>

<details>
<summary>**For uv users**</summary>

UV provides faster dependency resolution and installation. After
[installing UV](https://docs.astral.sh/uv/getting-started/installation/):

```bash
uv install
```

<details>
<summary>**Recommended: for mise users**</summary>

We recommend mise for a more reliable setup experience across different
operating systems. After
[installing mise](https://mise.jdx.dev/getting-started.html):

```bash
mise install  # Sets up Python 3.13.7, uv, and ruff automatically
mise run install # Installs the dependencies of the project
```

</details>

Once you have everything installed, you can play around with the
[example](example.py) script:

```bash
# If using mise/uv
uv run example.py

# If using standard Python
python example.py
```

## Project background

This project was originally developed by [@Ximaz](https://github.com/Ximaz), the
original repository was deleted or made private at some point during/after 2023.
I decided to continue development on my work, and have currently finished
completely refactoring the codebase to fix changes made by the sites we support.

The
[original implementation](https://github.com/totallynotdavid/megaloader/tree/9adeffe2d4055d26f9db2b7fcbf6f92de0aca628)
has been largely rewritten with my own opinionade ideas. My focus is on the
following plugins (Bunkr, PixelDrain, Cyberdrop, and GoFile, which I decided to
call core) while providing best-effort support for the extended set.

> [!TIP]
> If you encounter issues with any plugin, please report them through the
> [GitHub Issues](https://github.com/totallynotdavid/megaloader/issues) tracker.
> Include specific URLs, error messages (logs with DEBUG), and your Python
> version for faster troubleshooting.

## Understanding the architecture

The package has a plugin-based architecture. Each supported platform is
implemented as a separate plugin that inherits from a `BasePlugin` abstract base
class.

Every plugin implements two methods:

- `export()` - Parses platform-specific pages and extracts file information
- `download_file()` - Handles the actual file retrieval and storage

An `Item` dataclass is used to pass information between these operations. See
[megaloader/plugin.py](megaloader/plugin.py?plain=1#L7):

```python
@dataclass
class Item:
    url: str                                   # Direct download URL
    filename: str                              # Suggested filename
    album_title: Optional[str] = None          # Album/collection name
    file_id: Optional[str] = None              # Platform-specific ID
    metadata: Optional[dict[str, Any]] = None  # Additional platform data
```

### Advanced usage

Some plugins support additional configuration options.

For example, PixelDrain has an additional `use_proxy` option which lets you use
a list of proxies provided by [@sh13y](https://github.com/sh13y) via
[Cloudflare workers](https://github.com/sh13y/pixeldrain-ratelimit-bypasser). Of
course, this can help with rate limiting issues but the caveat is that you have
to trust his code/deployments[^1]. This option is turned off by default.

```python
download(
    "https://pixeldrain.com/l/nH4ZKt3b",
    "./downloads",
    use_proxy=True
)
```

GoFile allows users to put a password to access their files/albums. The module
support this via the password prop.

```python
download(
    "https://gofile.io/d/protected_folder",
    "./downloads",
    password="secret123"
)
```

For maximum control over the download process, you can import a specific plugin
and use it. If you intend to provide a service using this package, you should
handle rate limiting, caching, URL validation by yourself. This package is not
designed for high stressed scenarios (for now).

To use the plugin class, you can do something like this:

```python
from megaloader.plugins import Cyberdrop

plugin = Cyberdrop("https://cyberdrop.me/a/album_id")

# Extract all items first (useful for progress tracking)
items = list(plugin.export())
print(f"Found {len(items)} files to download")

# Download with custom logic
for i, item in enumerate(items):
    print(f"Downloading {i+1}/{len(items)}: {item.filename}")
    success = plugin.download_file(item, "./downloads/")
    if not success:
        print(f"Failed to download {item.filename}")
```

## How to contribute

We welcome contributions whether you're fixing bugs, improving existing plugins,
or adding support for new platforms.

Our development workflow includes several automated tasks for code quality:

```bash
mise run fix     # Format code and apply safe automated fixes via ruff
mise run mypy    # Run comprehensive type checking
mise run export  # Update requirements.txt from pyproject.toml
```

All contributions must meet our automated CI pipeline requirements which include
[type safety](.github/workflows/checks.yml) (you'll be fine if you pass
`mise run mypy`), [code style](.github/workflows/checks.yml) (`mise run fix`)
and [security](.github/workflows/codeql.yml) (codeql).

### Creating new plugins

When developing plugins for new platforms, follow these guidelines:

1. **Inherit from BasePlugin** and implement both required methods
2. **Register your plugin** in the domain registry for automatic detection. See
   [plugins/**init**.py](megaloader/plugins/__init__.py)
3. (Optional) **Try to follow existing patterns** for consistency with the
   existing codebase

Here's a minimal plugin template:

```python
class NewPlatformPlugin(BasePlugin):
    def __init__(self, url: str, **kwargs: Any) -> None:
        super().__init__(url, **kwargs)
        # Initialize session, configure headers, etc.

    def export(self) -> Generator[Item, None, None]:
        # Parse the URL and extract file information
        # Yield Item objects with download metadata
        pass

    def download_file(self, item: Item, output_dir: str) -> bool:
        # Handle actual file download and storage
        # Return success/failure status
        return True
```

### Technical details

**Dependencies**: The runtime has a minimal footprint with just three core
dependencies - `requests` for HTTP operations, `beautifulsoup4` for HTML
parsing, and `lxml` as the high-performance parser backend for `beautifulsoup4`.
Development dependencies include `ruff` for code quality and `mypy` for type
safety. The [requirements.txt](requirements.txt) has a more extensive list but
includes dependencies of our dependencies.

**Configuration**: The `pyproject.toml` serves as the central configuration
file, while `mise.toml` provides development environment automation with exact
tool versions and task orchestration. Both ruff and mypy are configured in
pyproject.toml.

## Getting help

**Bug Reports**: Use our
[GitHub Issues](https://github.com/totallynotdavid/megaloader/issues) tracker.
Include Python version, complete error messages, and specific URLs that are
failing.

**Feature Requests**: Also through GitHub Issues. Describe your use case and the
platform you'd like to see supported.

**General Questions**: GitHub Discussions are appropriate for general questions
about usage or architecture.

Remember to include relevant technical details like your Python version,
dependency versions (you can get this with `uv tree` if using UV), and complete
stack traces when reporting issues. This information significantly speeds up the
debugging process and helps us provide better support.

[^1]:
    The repo may not be the code deployed on the actual worker and could
    introduce you to man in the middle attacks.
