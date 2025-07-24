class MegaloaderError(Exception):
    """Base exception for errors originating within the megaloader package."""

    pass


class PluginNotFoundError(MegaloaderError):
    """Raised when a suitable plugin cannot be found for a given URL."""

    pass


class DownloadError(MegaloaderError):
    """Raised for errors specifically related to the download process."""

    pass
