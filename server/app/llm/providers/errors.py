class ProviderError(Exception):
    """Base provider error."""


class ProviderTimeoutError(ProviderError):
    """Raised when provider request times out."""


class ProviderHTTPError(ProviderError):
    """Raised on non-success HTTP response."""
