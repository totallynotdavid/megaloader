import click

from megaloader.plugins import PLUGIN_REGISTRY
from megaloader_cli.commands import download_command, extract_command
from megaloader_cli.utils import console, setup_logging


@click.group()
@click.version_option(prog_name="megaloader")
def cli() -> None:
    """
    Megaloader - Extract and download content from file hosting platforms.

    Examples:
      megaloader extract https://pixeldrain.com/l/abc123
      megaloader download https://gofile.io/d/xyz456 ./downloads
      megaloader plugins
    """


@cli.command(name="extract")
@click.argument("url")
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output JSON instead of human-readable text",
)
@click.option("-v", "--verbose", is_flag=True, help="Enable debug logging")
def extract_cmd(url: str, output_json: bool, verbose: bool) -> None:
    """
    Extract metadata from URL without downloading (dry run).

    Shows what would be downloaded including filenames, sizes, and URLs.
    """
    setup_logging(verbose)
    extract_command(url, output_json)


@cli.command(name="download")
@click.argument("url")
@click.argument("output_dir", type=click.Path(), default="./downloads")
@click.option("-v", "--verbose", is_flag=True, help="Enable debug logging")
@click.option(
    "--flat",
    is_flag=True,
    help="Save all files to output_dir (no collection subfolders)",
)
@click.option(
    "--filter",
    "pattern",
    help="Filter files by glob pattern (e.g., *.jpg, *.mp4)",
)
@click.option(
    "--password",
    help="Password for protected content (Gofile)",
)
def download_cmd(
    url: str,
    output_dir: str,
    verbose: bool,
    flat: bool,
    pattern: str | None,
    password: str | None,
) -> None:
    """
    Download content from URL to OUTPUT_DIR.

    By default, files are organized into subfolders by collection.
    Use --flat to disable this behavior.
    """
    setup_logging(verbose)

    options = {}
    if password:
        options["password"] = password

    download_command(url, output_dir, flat, pattern, options)


@cli.command(name="plugins")
def list_plugins_cmd() -> None:
    """List all supported websites and domains."""
    console.print("\n[bold]Supported Platforms:[/bold]\n")

    for domain in sorted(PLUGIN_REGISTRY.keys()):
        plugin = PLUGIN_REGISTRY[domain]
        console.print(f"  • [cyan]{domain:<20}[/cyan] ({plugin.__name__})")

    console.print()


if __name__ == "__main__":
    cli()
