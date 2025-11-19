import sys

from fnmatch import fnmatch
from pathlib import Path

from megaloader import Item, extract
from megaloader.exceptions import MegaloaderError, UnsupportedDomainError
from megaloader.plugins import get_plugin_class
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

from megaloader_cli.io import download_item
from megaloader_cli.utils import console, sanitize_filename


def resolve_plugin_name(url: str) -> str | None:
    """Helper to identify which plugin handles a URL for UI feedback."""
    from urllib.parse import urlparse

    domain = urlparse(url).netloc
    cls = get_plugin_class(domain)
    return cls.__name__ if cls else None


def process_extraction(url: str, output_json: bool) -> None:
    """Handle the 'extract' command logic."""
    try:
        if plugin_name := resolve_plugin_name(url):
            console.print(
                f"[green]✓[/green] Detected Plugin: [bold]{plugin_name}[/bold]"
            )

        # Convert generator to list for display/count
        items = list(extract(url))

        if output_json:
            _print_json(url, items)
        else:
            _print_human_readable(items)

    except (MegaloaderError, UnsupportedDomainError) as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


def process_download(
    url: str, output_dir: str, no_subdirs: bool, pattern: str | None
) -> None:
    """Handle the 'download' command logic."""
    try:
        if plugin_name := resolve_plugin_name(url):
            console.print(
                f"[green]✓[/green] Detected Plugin: [bold]{plugin_name}[/bold]"
            )

        with console.status("[cyan]Fetching metadata...[/cyan]"):
            items = list(extract(url))

        # Filter
        if pattern:
            initial_count = len(items)
            items = [i for i in items if fnmatch(i.filename, pattern)]
            console.print(
                f"[dim]Filtered from {initial_count} to {len(items)} items[/dim]"
            )

        if not items:
            console.print("[yellow]⚠ No items found to download.[/yellow]")
            return

        console.print(
            f"[green]✓[/green] Queued [bold]{len(items)}[/bold] items for download."
        )
        _run_download_loop(items, Path(output_dir), no_subdirs)

    except (MegaloaderError, UnsupportedDomainError) as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


def _run_download_loop(items: list[Item], base_dir: Path, no_subdirs: bool) -> None:
    """Orchestrate the download progress bar and IO calls."""
    success_count = 0
    failed_count = 0

    # Configure the progress bar layout
    progress = Progress(
        TextColumn("[bold blue]{task.fields[filename]}", justify="right"),
        BarColumn(bar_width=None),
        "[progress.percentage]{task.percentage:>3.0f}%",
        "•",
        DownloadColumn(),
        "•",
        TransferSpeedColumn(),
        "•",
        TimeRemainingColumn(),
        console=console,
    )

    with progress:
        # Create a main tracking task
        overall_task = progress.add_task(
            "Overall Progress", total=len(items), filename="Batch"
        )

        for item in items:
            # Calculate path
            dest_dir = base_dir
            if not no_subdirs and item.album:
                dest_dir = base_dir / sanitize_filename(item.album)

            full_path = dest_dir / sanitize_filename(item.filename)

            # Add individual download task
            task_id = progress.add_task("download", filename=item.filename, start=False)

            # Perform IO
            result = download_item(item, full_path, progress, task_id)

            if result:
                success_count += 1
            else:
                failed_count += 1

            # Clean up UI
            progress.remove_task(task_id)
            progress.advance(overall_task)

    # Final Summary
    console.print()
    if failed_count == 0:
        console.print(
            f"[bold green]Success![/bold green] All {success_count} files downloaded."
        )
        console.print(f"Location: {base_dir.absolute()}")
    else:
        console.print(
            f"[bold yellow]Finished with errors.[/bold yellow] {success_count} ok, {failed_count} failed."
        )
        sys.exit(1)


def _print_json(url: str, items: list[Item]) -> None:
    import dataclasses

    data = {
        "source": url,
        "count": len(items),
        "items": [dataclasses.asdict(i) for i in items],
    }
    console.print_json(data=data)


def _print_human_readable(items: list[Item]) -> None:
    console.print(f"\n[bold]Found {len(items)} items:[/bold]\n")
    for i, item in enumerate(items, 1):
        meta_info = f"[dim]({item.meta})[/dim]" if item.meta else ""
        console.print(f"  [cyan]{i:02d}.[/cyan] {item.filename} {meta_info}")
        if item.album:
            console.print(f"      [dim]Album: {item.album}[/dim]")
