from pathlib import Path

import requests

from megaloader.item import DownloadItem
from rich.progress import Progress, TaskID


def download_file(
    item: DownloadItem,
    destination: Path,
    progress: Progress,
    task_id: TaskID,
) -> bool:
    """Return True when the file was written or already exists, False on failure."""
    try:
        if destination.exists():
            progress.console.print(
                f"[yellow]⊙[/yellow] Skipped (exists): {item.filename}"
            )
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

            with destination.open("wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        progress.advance(task_id, len(chunk))

        return True

    except (requests.RequestException, OSError) as e:
        progress.console.print(f"[red]✗[/red] Failed: {item.filename} ({e!s})")

        if destination.exists():
            destination.unlink(missing_ok=True)

        return False
