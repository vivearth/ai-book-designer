class ProviderError(Exception):
    """Base provider error."""


class ProviderConfigurationError(ProviderError):
    """Raised when provider configuration is invalid."""


class ProviderTimeoutError(ProviderError):
    """Raised when provider request times out."""


class ProviderHTTPError(ProviderError):
    """Raised on non-success HTTP response."""
