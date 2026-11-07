from pathlib import Path

import requests

from megaloader.item import DownloadItem
from rich.markup import escape
from rich.progress import Progress, TaskID


def download_file(
    item: DownloadItem,
    destination: Path,
    progress: Progress,
    task_id: TaskID,
) -> bool:
    """Return True when the file was written or already exists, False on failure.

    The body goes to a sibling .part file that replaces the destination only
    when complete, so an interrupted run never leaves a truncated file that the
    next run would skip as existing.
    """
    name = escape(item.filename)
    partial = destination.with_name(destination.name + ".part")

    try:
        if destination.exists():
            progress.console.print(f"[yellow]⊙[/yellow] Skipped (exists): {name}")
            progress.advance(task_id, 100)
            return True

        destination.parent.mkdir(parents=True, exist_ok=True)

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            **item.headers,
        }

        with requests.get(
            item.download_url,
            stream=True,
            timeout=60,
            headers=headers,
        ) as response:
            response.raise_for_status()

            total_size = int(response.headers.get("content-length", 0))
            progress.update(task_id, total=total_size)

            with partial.open("wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        progress.advance(task_id, len(chunk))

        partial.replace(destination)
        return True

    except (requests.RequestException, OSError) as e:
        progress.console.print(f"[red]✗[/red] Failed: {name} ({escape(str(e))})")
        return False

    finally:
        partial.unlink(missing_ok=True)
