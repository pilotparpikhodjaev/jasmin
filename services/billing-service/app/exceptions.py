class BillingError(Exception):
    """Base class for billing service exceptions."""


class NotFoundError(BillingError):
    """Raised when an entity cannot be found."""


class InsufficientBalanceError(BillingError):
    """Raised when an account lacks sufficient funds or credit."""


class DuplicateMessageError(BillingError):
    """Raised when a duplicate message_id charge is attempted."""

