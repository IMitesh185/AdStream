"""Domain contracts, exceptions, and exact integer-micros AdTech metrics."""

from adstream.domain.exceptions import (
    AdStreamError,
    CircuitOpenError,
    DuplicateEventError,
    InsufficientBudgetError,
    InvalidEventError,
    RateLimitExceededError,
    SchemaCompatibilityError,
    TenantAuthorizationError,
)
from adstream.domain.metrics import (
    calculate_cpa_micros,
    calculate_cpc_micros,
    calculate_cpm_micros,
    calculate_ctr_percent,
    calculate_cvr_percent,
    calculate_platform_fee_micros,
    calculate_publisher_payout_micros,
    calculate_roas,
    micros_to_usd,
    usd_to_micros,
)

__all__ = [
    "AdStreamError",
    "CircuitOpenError",
    "DuplicateEventError",
    "InsufficientBudgetError",
    "InvalidEventError",
    "RateLimitExceededError",
    "SchemaCompatibilityError",
    "TenantAuthorizationError",
    "calculate_cpa_micros",
    "calculate_cpc_micros",
    "calculate_cpm_micros",
    "calculate_ctr_percent",
    "calculate_cvr_percent",
    "calculate_platform_fee_micros",
    "calculate_publisher_payout_micros",
    "calculate_roas",
    "micros_to_usd",
    "usd_to_micros",
]
