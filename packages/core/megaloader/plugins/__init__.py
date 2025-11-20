from megaloader.plugin import BasePlugin
from megaloader.plugins.bunkr import Bunkr
from megaloader.plugins.cyberdrop import Cyberdrop
from megaloader.plugins.fanbox import Fanbox
from megaloader.plugins.fapello import Fapello
from megaloader.plugins.gofile import Gofile
from megaloader.plugins.pixeldrain import PixelDrain
from megaloader.plugins.pixiv import Pixiv
from megaloader.plugins.rule34 import Rule34
from megaloader.plugins.thothub_to import ThothubTO
from megaloader.plugins.thothub_vip import ThothubVIP
from megaloader.plugins.thotslife import Thotslife


PLUGIN_REGISTRY: dict[str, type[BasePlugin]] = {
    "bunkr.si": Bunkr,
    "bunkr.la": Bunkr,
    "bunkr.is": Bunkr,
    "bunkr.ru": Bunkr,
    "bunkr.su": Bunkr,
    "cyberdrop.me": Cyberdrop,
    "cyberdrop.to": Cyberdrop,
    "fanbox.cc": Fanbox,
    "fapello.com": Fapello,
    "gofile.io": Gofile,
    "pixeldrain.com": PixelDrain,
    "pixiv.net": Pixiv,
    "rule34.xxx": Rule34,
    "thothub.ch": ThothubTO,
    "thothub.to": ThothubTO,
    "thothub.vip": ThothubVIP,
    "thotslife.com": Thotslife,
}

# Domains that support subdomains (e.g., creator.fanbox.cc)
SUBDOMAIN_SUPPORTED: set[str] = {"fanbox.cc"}


def get_plugin_class(domain: str) -> type[BasePlugin] | None:
    """
    Resolve domain to plugin class.

    Resolution order:
    1. Exact match in PLUGIN_REGISTRY
    2. Subdomain match for supported domains
    3. Partial match (fallback for domain variations)

    Args:
        domain: Normalized domain from URL (e.g., "pixiv.net")

    Returns:
        Plugin class or None if unsupported
    """
    domain = domain.lower().strip()

    # Exact match
    if domain in PLUGIN_REGISTRY:
        return PLUGIN_REGISTRY[domain]

    # Subdomain support (e.g., creator.fanbox.cc -> fanbox.cc)
    for base_domain in SUBDOMAIN_SUPPORTED:
        if domain.endswith(f".{base_domain}") and base_domain in PLUGIN_REGISTRY:
            return PLUGIN_REGISTRY[base_domain]

    # Partial match fallback (e.g., www.pixiv.net -> pixiv.net)
    for registered_domain, plugin_class in PLUGIN_REGISTRY.items():
        if registered_domain in domain:
            return plugin_class

    return None


__all__ = ["PLUGIN_REGISTRY", "get_plugin_class"]
