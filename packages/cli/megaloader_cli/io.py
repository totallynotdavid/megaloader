from pathlib import Path

import requests

from megaloader import Item
from rich.progress import Progress, TaskID


def download_item(
    item: Item, destination: Path, progress: Progress, task_id: TaskID
) -> bool:
    """
    Stream a file from URL to Disk with progress updates.

    Args:
        item: The metadata item containing URL and filename.
        destination: Full path to save the file (dir + filename).
        progress: Rich progress instance.
        task_id: The specific task ID to update in the progress bar.

    Returns:
        bool: True if successful or skipped, False if failed.
    """
    try:
        if destination.exists():
            # Skip logic could be enhanced (check size?), keeping it simple for now
            progress.console.print(
                f"[yellow]⊙[/yellow] Skipped (exists): {item.filename}"
            )
            progress.advance(task_id, 100)  # visually complete the bar
            return True

        destination.parent.mkdir(parents=True, exist_ok=True)

        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        if item.meta and "referer" in item.meta:
            headers["Referer"] = item.meta["referer"]

        with requests.get(
            item.url, stream=True, timeout=60, headers=headers
        ) as response:
            response.raise_for_status()

            total_length = int(response.headers.get("content-length", 0))
            progress.update(task_id, total=total_length)

            with Path(destination).open("wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        progress.advance(task_id, len(chunk))

        return True

    except (requests.RequestException, OSError) as e:
        # We print to console here so it appears above the progress bar
        progress.console.print(f"[red]✗[/red] Failed: {item.filename} ({e!s})")
        if destination.exists():
            destination.unlink(missing_ok=True)
        return False
