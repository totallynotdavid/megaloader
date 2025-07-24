from .bunkr import Bunkr
from .pixeldrain import PixelDrain

# Domain to plugin mapping
PLUGIN_REGISTRY = {
    # Bunkr domains
    "bunkr.si": Bunkr,
    "bunkr.la": Bunkr,
    "bunkr.is": Bunkr,
    "bunkr.ru": Bunkr,
    "bunkr.su": Bunkr,
    "bunkr": Bunkr,
    # PixelDrain domains
    "pixeldrain.com": PixelDrain,
    "pixeldrain": PixelDrain,
}


def get_plugin_class(domain: str):
    """
    Get plugin class for a domain.

    Args:
        domain: Domain name or identifier

    Returns:
        Plugin class, or None if no plugin found
    """
    domain = domain.lower().strip()

    # Direct match first
    if domain in PLUGIN_REGISTRY:
        return PLUGIN_REGISTRY[domain]

    # Check for subdomain matches
    for key, plugin_cls in PLUGIN_REGISTRY.items():
        if key in domain:
            return plugin_cls

    return None


__all__ = ["Bunkr", "PixelDrain", "get_plugin_class"]
