class ProviderError(Exception):
    """Base provider error."""


class ProviderConfigurationError(ProviderError):
    """Raised when provider configuration is invalid."""


class ProviderTimeoutError(ProviderError):
    """Raised when provider request times out."""


class ProviderHTTPError(ProviderError):
    """Raised on non-success HTTP response."""

    def __init__(self, message: str, *, status: int | None = None, body_preview: str | None = None) -> None:
        self.status = status
        self.body_preview = body_preview
        detail = message
        if status is not None:
            detail = f"{detail} status={status}"
        if body_preview:
            detail = f"{detail} body_preview={body_preview[:400]}"
        super().__init__(detail)
