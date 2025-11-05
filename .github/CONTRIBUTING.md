# For contributors

We welcome contributions ranging from bug fixes to new platform support. The
development workflow emphasizes code quality through automated tooling and
comprehensive type checking.

The project includes several automated tasks that maintain code quality and
consistency. These tools are configured in [pyproject.toml](../pyproject.toml)
([ruff](../pyproject.toml?plain=1#L32) and
[mypy](../pyproject.toml?plain=1#L69)) and can be executed through mise:

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
implementing the two core methods, with registration in the
[domain registry](../megaloader/plugins/__init__.py?plain=1#L16) for automatic
URL detection.

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
[`megaloader/plugins/__init__.py`](../megaloader/plugins/__init__.py) to enable
automatic URL detection.

### Technical details

The runtime maintains a minimal dependency footprint with three core libraries:

- `requests` handles HTTP operations and session management,
- `beautifulsoup4` provides HTML parsing capabilities, and
- `lxml` serves as the high-performance parser backend.

Development dependencies include `ruff` for code formatting and linting, plus
`mypy` for static type checking. The complete dependency tree is available in
[requirements.txt](../requirements.txt).

Configuration management centralizes around [pyproject.toml](../pyproject.toml),
which contains settings for all tools including ruff, mypy, and packaging
metadata. The [mise.toml](../mise.toml) file provides development environment
automation with exact tool versions and task orchestration for consistent
development experiences.

## Submitting contributions

To ensure a smooth process, please follow these steps:

1.  Start by **forking the repository** and creating a new branch for your
    feature or bug fix; all work should be done in a dedicated feature branch.
2.  Always **run the quality checks** using `mise run fix` and `mise run mypy`
    to ensure your code meets the project's standards.
3.  Before opening a PR (pull request), please **test your changes** thoroughly.
    This is especially critical if you're adding a new plugin. (A tests module
    to automate this is planned for the future).
4.  Once your work is ready, you can **submit a PR (pull request)**. Please
    include a clear description of the problem it addresses and the solution
    you've implemented.

### Pull request guidelines

PRs should remain focused, addressing a single feature or bug fix at a time. Use
descriptive commit messages and provide enough context in the pull request
description to make the review process straightforward. Update any affected
documentation, particularly if your changes alter the public API or development
workflow.

To discuss design choices, integrations, or open questions, please use
[GitHub Discussions](https://github.com/totallynotdavid/megaloader/discussions).

### Reporting bugs

Bug reports should be submitted through
[GitHub Discussions](https://github.com/totallynotdavid/megaloader/discussions)
rather than GitHub Issues. Include your Python version, complete error messages,
stack traces, problematic URLs, and DEBUG-level logging output.
