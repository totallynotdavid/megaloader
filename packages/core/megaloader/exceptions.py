class MegaloaderError(Exception):
    """Base exception for all megaloader errors."""


class ExtractionError(MegaloaderError):
    """Extraction failure with normalized metadata for downstream policy."""

    def __init__(
        self,
        detail: str,
        *,
        source: str | None = None,
        url: str | None = None,
        http_status: int | None = None,
        provider_status: str | None = None,
        category: str = "unknown",
        cause: Exception | None = None,
    ) -> None:
        super().__init__(detail)
        self.detail = detail
        self.source = source
        self.url = url
        self.http_status = http_status
        self.provider_status = provider_status
        self.category = category
        self.cause = cause

    def __str__(self) -> str:
        return self.detail


class UnsupportedDomainError(MegaloaderError):
    """No plugin available for this domain."""

    def __init__(self, domain: str) -> None:
        super().__init__(f"No plugin found for domain: {domain}")
        self.domain = domain
