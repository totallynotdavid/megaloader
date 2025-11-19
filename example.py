"""
An annotated example showing how to use the megaloader library.

This script extracts download metadata from a supported URL and logs the results.
It does not perform actual downloads—see the CLI (packages/cli) or API (api) for that.
"""

import logging

import megaloader as mgl

from megaloader.exceptions import ExtractionError, UnsupportedDomainError


logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    """
    Extract and display metadata for items in a given URL.

    Uses a sample URL from test_urls.py for demonstration.
    Replace with your own URL as needed.
    """
    url = "https://pixeldrain.com/l/DDGtvvTU"

    try:
        # Get a lazy generator of downloadable items (no network calls yet)
        items = mgl.extract(url)

        # Iterate over items to fetch metadata (triggers HTTP requests)
        for item in items:
            logger.info(
                "Found item: %s | Download URL: %s | Size: %s bytes",
                item.filename,
                item.download_url,
                item.size_bytes or "unknown",
            )

    except UnsupportedDomainError as e:
        logger.exception("Unsupported domain: %s (no plugin available)", e.domain)
    except ExtractionError:
        logger.exception("Failed to extract from URL")


if __name__ == "__main__":
    main()
