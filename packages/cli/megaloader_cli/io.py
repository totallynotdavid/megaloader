from pathlib import Path

import requests
from rich.progress import Progress, TaskID

from megaloader.item import DownloadItem


def download_file(
    item: DownloadItem,
    destination: Path,
    progress: Progress,
    task_id: TaskID,
) -> bool:
    """
    Download a file with progress tracking.

    Args:
        item: Download metadata including URL and required headers
        destination: Full path where file will be saved
        progress: Rich progress instance for UI updates
        task_id: Task ID for this specific download

    Returns:
        True if successful or skipped, False if failed
    """
    try:
        # Skip if file already exists
        if destination.exists():
            progress.console.print(
                f"[yellow]⊙[/yellow] Skipped (exists): {item.filename}"
            )
            progress.advance(task_id, 100)
            return True

        # Ensure parent directory exists
        destination.parent.mkdir(parents=True, exist_ok=True)

        # Build headers
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            **item.headers,
        }

        # Stream download
        with requests.get(
            item.download_url,
            stream=True,
            timeout=60,
            headers=headers,
        ) as response:
            response.raise_for_status()

            # Get file size for progress bar
            total_size = int(response.headers.get("content-length", 0))
            progress.update(task_id, total=total_size)

            # Write to disk in chunks
            with destination.open("wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        progress.advance(task_id, len(chunk))

        return True

    except (requests.RequestException, OSError) as e:
        # Print error above progress bar
        progress.console.print(f"[red]✗[/red] Failed: {item.filename} ({e!s})")

        # Clean up partial download
        if destination.exists():
            destination.unlink(missing_ok=True)

        return False
