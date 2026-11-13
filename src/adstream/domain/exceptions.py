"""Typed domain exceptions for AdStream."""


class AdStreamError(Exception):
    """Base exception for all AdStream domain errors."""

    error_code: str = "ADSTREAM_ERROR"

    def __init__(self, message: str, *, error_code: str | None = None) -> None:
        super().__init__(message)
        if error_code is not None:
            self.error_code = error_code


class InvalidEventError(AdStreamError):
    error_code = "INVALID_EVENT"


class SchemaCompatibilityError(AdStreamError):
    error_code = "UNSUPPORTED_SCHEMA_VERSION"


class InsufficientBudgetError(AdStreamError):
    error_code = "INSUFFICIENT_BUDGET"


class DuplicateEventError(AdStreamError):
    error_code = "DUPLICATE_EVENT"


class TenantAuthorizationError(AdStreamError):
    error_code = "TENANT_FORBIDDEN"


class RateLimitExceededError(AdStreamError):
    error_code = "RATE_LIMIT_EXCEEDED"

    def __init__(self, message: str, *, retry_after_seconds: float) -> None:
        super().__init__(message)
        self.retry_after_seconds = retry_after_seconds


class CircuitOpenError(AdStreamError):
    error_code = "CIRCUIT_OPEN"
