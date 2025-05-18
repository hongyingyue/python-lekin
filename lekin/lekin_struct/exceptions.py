"""
Custom exceptions for the lekin package.
"""


class LekinError(Exception):
    """Base exception class for lekin package."""

    pass


class ValidationError(LekinError):
    """Raised when validation of input data fails."""

    pass


class SchedulingError(LekinError):
    """Raised when scheduling operations fail."""

    pass


class ResourceError(LekinError):
    """Raised when resource-related operations fail."""

    pass


class OperationError(LekinError):
    """Raised when operation-related operations fail."""

    pass


class RouteError(LekinError):
    """Raised when route-related operations fail."""

    pass
