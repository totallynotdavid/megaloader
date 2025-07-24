class MegaloaderError(Exception):
    """Base exception for all megaloader errors."""


class PluginError(MegaloaderError):
    """Plugin-related errors."""


class DownloadError(MegaloaderError):
    """Download-related errors."""
