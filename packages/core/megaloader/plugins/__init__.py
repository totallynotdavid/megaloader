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
    "bunkr": Bunkr,
    "cyberdrop.me": Cyberdrop,
    "cyberdrop.to": Cyberdrop,
    "cyberdrop": Cyberdrop,
    "fanbox.cc": Fanbox,
    "fapello.com": Fapello,
    "gofile.io": Gofile,
    "pixeldrain.com": PixelDrain,
    "pixiv.net": Pixiv,
    "rule34.xxx": Rule34,
    "thothub.to": ThothubTO,
    "thothub.vip": ThothubVIP,
    "thotslife.com": Thotslife,
}

SUBDOMAIN_SUPPORTED_DOMAINS: set[str] = {"fanbox.cc"}


def get_plugin_class(domain: str) -> type[BasePlugin] | None:
    """Resolves a domain string to a Plugin class."""
    domain = domain.lower().strip()

    if domain in PLUGIN_REGISTRY:
        return PLUGIN_REGISTRY[domain]

    for supported_domain in SUBDOMAIN_SUPPORTED_DOMAINS:
        if (
            domain.endswith("." + supported_domain)
            and supported_domain in PLUGIN_REGISTRY
        ):
            return PLUGIN_REGISTRY[supported_domain]

    for key, plugin_cls in PLUGIN_REGISTRY.items():
        if key in domain:
            return plugin_cls

    return None


__all__ = ["get_plugin_class"]
