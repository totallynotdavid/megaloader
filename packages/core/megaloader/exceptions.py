class MegaloaderError(Exception):
    """Base exception for all megaloader errors."""


class ExtractionError(MegaloaderError):
    """Failed to extract items from URL."""


class UnsupportedDomainError(MegaloaderError):
    """No plugin available for this domain."""

    def __init__(self, domain: str) -> None:
        super().__init__(f"No plugin found for domain: {domain}")
