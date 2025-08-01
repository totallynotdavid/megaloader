from megaloader.plugin import BasePlugin
from megaloader.plugins.bunkr import Bunkr
from megaloader.plugins.cyberdrop import Cyberdrop
from megaloader.plugins.fapello import Fapello
from megaloader.plugins.gofile import Gofile
from megaloader.plugins.pixeldrain import PixelDrain


# Domain to plugin mapping
PLUGIN_REGISTRY: dict[str, type[BasePlugin]] = {
    # Bunkr domains
    "bunkr.si": Bunkr,
    "bunkr.la": Bunkr,
    "bunkr.is": Bunkr,
    "bunkr.ru": Bunkr,
    "bunkr.su": Bunkr,
    "bunkr": Bunkr,
    # Cyberdrop domains
    "cyberdrop.me": Cyberdrop,
    "cyberdrop.to": Cyberdrop,
    "cyberdrop": Cyberdrop,
    # Fapello domains
    "fapello.com": Fapello,
    # Gofile domains
    "gofile.io": Gofile,
    # PixelDrain domains
    "pixeldrain.com": PixelDrain,
}


def get_plugin_class(domain: str) -> type[BasePlugin] | None:
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


__all__ = [
    "Bunkr",
    "Cyberdrop",
    "Fapello",
    "Gofile",
    "PixelDrain",
    "get_plugin_class",
]
