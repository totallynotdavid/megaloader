"""
Megaloader CLI - Command-line interface for downloading content.

This CLI provides a simple interface to download files from supported platforms
using the megaloader library.
"""

import logging
import sys

from pathlib import Path

import click

from megaloader import download
from megaloader.exceptions import MegaloaderError
from megaloader.plugins import get_plugin_class
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import Progress, SpinnerColumn, TextColumn


console = Console()


def setup_logging(*, verbose: bool) -> None:
    """Configure logging with rich output."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(message)s",
        handlers=[RichHandler(console=console, rich_tracebacks=True)],
    )


@click.group()
@click.version_option(version="0.1.0", prog_name="megaloader")
def cli() -> None:
    """
    Megaloader - Download content from multiple file hosting platforms.

    Supports platforms like Bunkr, Cyberdrop, GoFile, PixelDrain, and more.
    """


@cli.command()
@click.argument("url")
@click.argument("output_dir", type=click.Path(), default="./downloads")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.option("--use-proxy", is_flag=True, help="Use proxy for downloads")
@click.option(
    "--no-subdirs",
    is_flag=True,
    help="Don't create album subdirectories",
)
def download_url(
    url: str,
    output_dir: str,
    *,
    verbose: bool,
    use_proxy: bool,
    no_subdirs: bool,
) -> None:
    """
    Download content from a URL.

    URL: The URL to download from
    OUTPUT_DIR: Directory to save files (default: ./downloads)
    """
    setup_logging(verbose=verbose)

    try:
        # Detect plugin
        plugin_class = get_plugin_class(url)
        if plugin_class:
            console.print(
                f"[green]✓[/green] Detected platform: {plugin_class.__name__}"
            )
        else:
            console.print(f"[yellow]⚠[/yellow] Using automatic detection for: {url}")

        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Download
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Downloading...", total=None)

            success = download(
                url,
                str(output_path),
                plugin_class=plugin_class,
                use_proxy=use_proxy,
                create_album_subdirs=not no_subdirs,
            )

            progress.update(task, completed=True)

        if success:
            console.print(f"[green]✓[/green] Download completed: {output_path}")
            sys.exit(0)
        else:
            console.print("[red]✗[/red] Download failed")
            sys.exit(1)

    except MegaloaderError as e:
        console.print(f"[red]✗[/red] Error: {e}")
        if verbose:
            console.print_exception()
        sys.exit(1)


@cli.command()
def list_plugins() -> None:
    """List all available plugins and supported platforms."""
    from megaloader.plugins import PLUGIN_REGISTRY

    console.print("\n[bold]Available Plugins:[/bold]\n")

    for domains, plugin_class in PLUGIN_REGISTRY.items():
        domain_list = ", ".join(domains) if isinstance(domains, tuple) else domains
        console.print(f"  • [cyan]{plugin_class.__name__}[/cyan]: {domain_list}")

    console.print()


if __name__ == "__main__":
    cli()
