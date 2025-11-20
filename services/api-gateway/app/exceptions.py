class GatewayError(Exception):
    """Base error for the API gateway."""


class AuthenticationError(GatewayError):
    """Raised when API key validation fails."""


class RateLimitExceeded(GatewayError):
    """Raised when an account exceeds its allowed TPS."""


class UpstreamError(GatewayError):
    """Raised when an upstream dependency fails."""


class BillingError(GatewayError):
    """Raised when billing service rejects a request."""

