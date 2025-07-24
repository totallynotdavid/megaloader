from .bunkr import Bunkr
from .pixeldrain import PixelDrain

# This allows for automatic plugin selection based on the URL domain.
# Identifiers without a specific domain (like 'bunkr') will match any URL containing that term.
_PLUGIN_REGISTRY = {
    "bunkr.si": Bunkr,
    "bunkr.la": Bunkr,
    "bunkr.is": Bunkr,
    "bunkr.ru": Bunkr,
    "bunkr.su": Bunkr,
    "bunkr": Bunkr,
    "pixeldrain.com": PixelDrain,
    "pixeldrain": PixelDrain,
}


def get_plugin_class(identifier: str):
    """Gets the plugin class for a given domain identifier."""
    identifier = identifier.lower().strip()
    if not identifier:
        return None

    # Direct match first (e.g., 'bunkr.si' -> Bunkr)
    if identifier in _PLUGIN_REGISTRY:
        return _PLUGIN_REGISTRY[identifier]

    # Fallback: Check if identifier contains a key (e.g., 'media.bunkr.la' contains 'bunkr')
    # This handles subdomains or slightly varied domains.
    for key, cls in _PLUGIN_REGISTRY.items():
        if key in identifier:
            return cls
    return None


# Re-export plugin classes for direct access (e.g., `from megaloader.plugins import Bunkr`)
__all__ = [
    "Bunkr",
    "PixelDrain",
    "get_plugin_class",
]
