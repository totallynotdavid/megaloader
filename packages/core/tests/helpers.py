import requests

from megaloader.item import DownloadItem


def validate_item(item: DownloadItem, site_name: str) -> list[str]:
    """
    Validate a DownloadItem has all required fields.
    Returns list of issues found (empty = valid).
    """
    issues = []

    # Critical: Must have download URL
    if not item.download_url:
        issues.append("Missing download_url")
    elif not item.download_url.startswith(("http://", "https://")):
        issues.append(f"Invalid download_url: {item.download_url}")

    # Critical: Must have filename
    if not item.filename:
        issues.append("Missing filename")
    elif item.filename.strip() == "":
        issues.append("Empty filename")

    # Warning: Suspicious patterns
    if item.filename and "undefined" in item.filename.lower():
        issues.append(f"Suspicious filename: {item.filename}")

    if item.filename and ".." in item.filename:
        issues.append(f"Path traversal in filename: {item.filename}")

    return issues


def check_url_accessible(url: str, timeout: int = 10) -> tuple[bool, str]:
    """
    Check if URL is accessible via HEAD request.
    Returns (is_accessible, status_message).
    """
    try:
        resp = requests.head(
            url,
            timeout=timeout,
            allow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0"},
        )

        if resp.status_code < 400:
            return True, f"OK ({resp.status_code})"
        return False, f"HTTP {resp.status_code}"

    except requests.Timeout:
        return False, "Timeout"
    except requests.RequestException as e:
        return False, f"Error: {e}"


def format_failure_message(
    site: str,
    url: str,
    items: list[DownloadItem],
    expected_min: int,
    issues: list[str],
) -> str:
    """Format a detailed failure message for CI."""
    msg = f"\n{'=' * 80}\n"
    msg += f"❌ {site} EXTRACTION FAILED\n"
    msg += f"{'=' * 80}\n"
    msg += f"URL: {url}\n"
    msg += f"Items extracted: {len(items)} (expected ≥{expected_min})\n"
    msg += "\nIssues found:\n"

    for issue in issues:
        msg += f"  • {issue}\n"

    if items:
        msg += "\nSample item:\n"
        sample = items[0]
        msg += f"  Filename: {sample.filename}\n"
        msg += f"  URL: {sample.download_url}\n"
        msg += f"  Collection: {sample.collection_name}\n"
        msg += f"  ID: {sample.source_id}\n"

    msg += "\n⚠️  ACTION REQUIRED:\n"
    msg += f"  1. Check if {site} changed their site structure\n"
    msg += f"  2. Review plugin: megaloader/plugins/{site.lower()}.py\n"
    msg += "  3. Update test URL if album was deleted\n"
    msg += f"{'=' * 80}\n"

    return msg
