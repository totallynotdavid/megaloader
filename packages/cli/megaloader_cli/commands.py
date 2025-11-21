import dataclasses
import sys

from fnmatch import fnmatch
from pathlib import Path
from typing import Any

import megaloader as mgl

from megaloader.exceptions import MegaloaderError
from megaloader.plugins import get_plugin_class
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

from megaloader_cli.io import download_file
from megaloader_cli.utils import console, sanitize_for_filesystem


def extract_command(url: str, output_json: bool) -> None:
    """
    Handle extract command logic.

    Fetches metadata and displays items without downloading.
    """
    try:
        # Show which plugin is being used
        if plugin_name := _get_plugin_name(url):
            console.print(f"[green]✓[/green] Using plugin: [bold]{plugin_name}[/bold]")

        # Stream items as they're discovered
        items = []
        with Progress(
            TextColumn("[bold blue]Extracting metadata..."),
            BarColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("", total=None)

            for item in mgl.extract(url):
                items.append(item)
                progress.update(task, advance=1)

        # Display results
        if output_json:
            _print_json(url, items)
        else:
            _print_human_readable(items)

    except MegaloaderError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


def download_command(
    url: str,
    output_dir: str,
    flat: bool,
    pattern: str | None,
    options: dict[str, Any],
) -> None:
    """
    Handle download command logic.

    Extracts metadata, filters items, and downloads files with progress tracking.
    """
    try:
        # Show which plugin is being used
        if plugin_name := _get_plugin_name(url):
            console.print(f"[green]✓[/green] Using plugin: [bold]{plugin_name}[/bold]")

        # Stream and collect items
        items = []
        with Progress(
            TextColumn("[bold blue]Discovering files..."),
            BarColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("", total=None)

            for item in mgl.extract(url, **options):
                items.append(item)
                progress.update(task, advance=1)

        # Apply filter if specified
        if pattern:
            original_count = len(items)
            items = [item for item in items if fnmatch(item.filename, pattern)]
            console.print(f"[dim]Filtered: {original_count} → {len(items)} files[/dim]")

        if not items:
            console.print("[yellow]⚠ No files to download.[/yellow]")
            return

        console.print(f"[green]✓[/green] Found [bold]{len(items)}[/bold] files.")

        # Download files with progress tracking
        _download_with_progress(items, Path(output_dir), flat)

    except MegaloaderError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


def _download_with_progress(
    items: list[mgl.DownloadItem],
    base_dir: Path,
    flat: bool,
) -> None:
    """
    Download all items with rich progress bars.

    Shows individual file progress and overall completion.
    """
    success_count = 0
    failed_count = 0

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
        # Overall progress tracker
        overall = progress.add_task(
            "Overall Progress",
            total=len(items),
            filename="Batch",
        )

        for item in items:
            # Determine destination path
            if flat or not item.collection_name:
                dest_dir = base_dir
            else:
                dest_dir = base_dir / sanitize_for_filesystem(item.collection_name)

            dest_path = dest_dir / sanitize_for_filesystem(item.filename)

            # Create individual file task
            file_task = progress.add_task(
                "download",
                filename=item.filename,
                start=False,
            )

            # Perform download
            if download_file(item, dest_path, progress, file_task):
                success_count += 1
            else:
                failed_count += 1

            # Update overall progress
            progress.remove_task(file_task)
            progress.advance(overall)

    # Summary
    console.print()
    if failed_count == 0:
        console.print(
            f"[bold green]✓ Success![/bold green] Downloaded {success_count} files."
        )
        console.print(f"[dim]Location: {base_dir.absolute()}[/dim]")
    else:
        console.print(
            f"[bold yellow]⚠ Completed with errors.[/bold yellow] "
            f"{success_count} succeeded, {failed_count} failed."
        )
        sys.exit(1)


def _get_plugin_name(url: str) -> str | None:
    """Get plugin name for UI feedback."""
    from urllib.parse import urlparse

    domain = urlparse(url).netloc
    plugin_class = get_plugin_class(domain)
    return plugin_class.__name__ if plugin_class else None


def _print_json(url: str, items: list[mgl.DownloadItem]) -> None:
    data = {
        "source": url,
        "count": len(items),
        "items": [dataclasses.asdict(item) for item in items],
    }
    console.print_json(data=data)


def _print_human_readable(items: list[mgl.DownloadItem]) -> None:
    console.print(f"\n[bold]Found {len(items)} files:[/bold]\n")

    for i, item in enumerate(items, 1):
        console.print(f"  [cyan]{i:02d}.[/cyan] {item.filename}")

        if item.collection_name:
            console.print(f"      [dim]Collection: {item.collection_name}[/dim]")

        if item.size_bytes:
            size_mb = item.size_bytes / (1024 * 1024)
            console.print(f"      [dim]Size: {size_mb:.2f} MB[/dim]")
