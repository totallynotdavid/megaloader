import logging
import re
import sys

from pathlib import Path

import click
import requests

from megaloader import Item, extract
from megaloader.exceptions import MegaloaderError, UnsupportedDomainError
from megaloader.plugins import get_plugin_class
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)


console = Console()
INVALID_DIR_CHARS = r'[<>:"/\\|?*]'


def setup_logging(*, verbose: bool) -> None:
    """Configure logging with rich output."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(message)s",
        handlers=[RichHandler(console=console, rich_tracebacks=True)],
    )


def sanitize_filename(name: str) -> str:
    """Remove invalid characters from filename or directory name."""
    return re.sub(INVALID_DIR_CHARS, "_", name).strip()


def download_file(
    item: Item, output_dir: Path, progress: Progress, task_id: int
) -> bool:
    """Download a single file with progress tracking."""
    try:
        output_path = output_dir / item.filename
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Skip if exists
        if output_path.exists():
            progress.console.print(
                f"[yellow]⊙[/yellow] Skipped (exists): {item.filename}"
            )
            return True

        # Prepare headers
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        if item.meta and "referer" in item.meta:
            headers["Referer"] = item.meta["referer"]

        # Download with progress
        response = requests.get(item.url, stream=True, timeout=60, headers=headers)
        response.raise_for_status()

        total_size = int(response.headers.get("content-length", 0))
        progress.update(task_id, total=total_size)

        with output_path.open("wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    progress.update(task_id, advance=len(chunk))

        progress.console.print(f"[green]✓[/green] Downloaded: {item.filename}")
        return True

    except (requests.RequestException, OSError) as e:
        progress.console.print(f"[red]✗[/red] Failed: {item.filename} ({e})")
        if output_path.exists():
            output_path.unlink()
        return False


@click.group()
@click.version_option(version="0.2.0", prog_name="megaloader")
def cli() -> None:
    """
    Megaloader - Extract and download content from file hosting platforms.

    Supports Bunkr, Cyberdrop, GoFile, PixelDrain, and more.
    """


@cli.command()
@click.argument("url")
@click.option(
    "--json", "output_json", is_flag=True, help="Output JSON instead of downloading"
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
def extract_cmd(url: str, *, output_json: bool, verbose: bool) -> None:
    """
    Extract metadata from a URL without downloading.

    URL: The URL to extract from
    """
    setup_logging(verbose=verbose)

    try:
        # Extract domain and detect plugin
        from urllib.parse import urlparse

        domain = urlparse(url).netloc
        plugin_class = get_plugin_class(domain)
        if plugin_class:
            console.print(f"[green]✓[/green] Plugin: {plugin_class.__name__}")

        items = extract(url)

        if output_json:
            data = {
                "url": url,
                "count": len(items),
                "items": [
                    {
                        "url": item.url,
                        "filename": item.filename,
                        "album": item.album,
                        "id": item.id,
                        "meta": item.meta,
                    }
                    for item in items
                ],
            }
            console.print_json(data=data)
        else:
            console.print(f"\n[bold]Found {len(items)} items:[/bold]\n")
            for i, item in enumerate(items, 1):
                console.print(f"  {i}. {item.filename}")
                if item.album:
                    console.print(f"     Album: {item.album}")

        sys.exit(0)

    except (MegaloaderError, UnsupportedDomainError) as e:
        console.print(f"[red]✗[/red] Error: {e}")
        sys.exit(1)


@cli.command()
@click.argument("url")
@click.argument("output_dir", type=click.Path(), default="./downloads")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.option("--no-subdirs", is_flag=True, help="Don't create album subdirectories")
@click.option("--filter", "pattern", help="Only download files matching pattern (glob)")
def download(
    url: str,
    output_dir: str,
    *,
    verbose: bool,
    no_subdirs: bool,
    pattern: str | None,
) -> None:
    """
    Download content from a URL.

    URL: The URL to download from
    OUTPUT_DIR: Directory to save files (default: ./downloads)
    """
    setup_logging(verbose=verbose)

    try:
        # Extract domain and detect plugin
        from urllib.parse import urlparse

        domain = urlparse(url).netloc
        plugin_class = get_plugin_class(domain)
        if plugin_class:
            console.print(f"[green]✓[/green] Plugin: {plugin_class.__name__}")

        # Extract items
        console.print("[cyan]⟳[/cyan] Extracting metadata...")
        items = extract(url)

        # Filter if pattern provided
        if pattern:
            from fnmatch import fnmatch

            items = [item for item in items if fnmatch(item.filename, pattern)]
            console.print(
                f"[cyan]⟳[/cyan] Filtered to {len(items)} items matching '{pattern}'"
            )

        if not items:
            console.print("[yellow]⚠[/yellow] No items found")
            sys.exit(0)

        console.print(f"[green]✓[/green] Found {len(items)} items")

        # Determine output directory
        base_output_dir = Path(output_dir)
        base_output_dir.mkdir(parents=True, exist_ok=True)

        # Download with progress
        success_count = 0
        failed_count = 0

        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            DownloadColumn(),
            TransferSpeedColumn(),
            TimeRemainingColumn(),
            console=console,
        ) as progress:
            for i, item in enumerate(items, 1):
                # Determine item output directory
                item_output_dir = base_output_dir
                if not no_subdirs and item.album:
                    safe_album = sanitize_filename(item.album)
                    if safe_album:
                        item_output_dir = base_output_dir / safe_album

                task = progress.add_task(
                    f"[cyan][{i}/{len(items)}][/cyan] {item.filename}",
                    total=None,
                )

                if download_file(item, item_output_dir, progress, task):
                    success_count += 1
                else:
                    failed_count += 1

                progress.remove_task(task)

        # Summary
        console.print()
        if failed_count == 0:
            console.print(
                f"[green]✓[/green] Success: Downloaded {success_count}/{len(items)} files"
            )
            console.print(f"[green]✓[/green] Location: {base_output_dir}")
            sys.exit(0)
        else:
            console.print(
                f"[yellow]⚠[/yellow] Partial: {success_count} succeeded, {failed_count} failed"
            )
            sys.exit(1)

    except (MegaloaderError, UnsupportedDomainError) as e:
        console.print(f"[red]✗[/red] Error: {e}")
        if verbose:
            console.print_exception()
        sys.exit(1)


@cli.command()
def list_plugins() -> None:
    """List all available plugins and supported platforms."""
    from megaloader.plugins import PLUGIN_REGISTRY

    console.print("\n[bold]Available Plugins:[/bold]\n")

    for domain, plugin_class in PLUGIN_REGISTRY.items():
        console.print(f"  • [cyan]{plugin_class.__name__}[/cyan]: {domain}")

    console.print()


if __name__ == "__main__":
    cli()
