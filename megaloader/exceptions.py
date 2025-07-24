class MegaloaderError(Exception):
    """Base exception for all megaloader errors."""

    pass


class PluginError(MegaloaderError):
    """Plugin-related errors."""

    pass


class DownloadError(MegaloaderError):
    """Download-related errors."""

    pass
