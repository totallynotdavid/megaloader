import click

from megaloader.plugins import PLUGIN_REGISTRY

from megaloader_cli.runner import process_download, process_extraction
from megaloader_cli.utils import console, setup_logging


@click.group()
@click.version_option(prog_name="megaloader")
def cli() -> None:
    """
    Megaloader - Extract and download content from file hosting platforms.
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
    Extract metadata from a URL (Dry Run).
    """
    setup_logging(verbose)
    process_extraction(url, output_json)


@cli.command(name="download")
@click.argument("url")
@click.argument("output_dir", type=click.Path(), default="./downloads")
@click.option("-v", "--verbose", is_flag=True, help="Enable debug logging")
@click.option(
    "--no-subdirs", is_flag=True, help="Flatten structure (don't create album folders)"
)
@click.option("--filter", "pattern", help="Glob pattern to filter files (e.g. *.jpg)")
def download_cmd(
    url: str, output_dir: str, verbose: bool, no_subdirs: bool, pattern: str | None
) -> None:
    """
    Download content from a URL to OUTPUT_DIR.
    """
    setup_logging(verbose)
    process_download(url, output_dir, no_subdirs, pattern)


@cli.command(name="plugins")
def list_plugins_cmd() -> None:
    """List supported websites."""
    console.print("\n[bold]Supported Platforms:[/bold]\n")
    # Sorting for better UX
    for domain in sorted(PLUGIN_REGISTRY.keys()):
        plugin = PLUGIN_REGISTRY[domain]
        console.print(f"  • [cyan]{domain:<20}[/cyan] ({plugin.__name__})")
    console.print()


if __name__ == "__main__":
    cli()
