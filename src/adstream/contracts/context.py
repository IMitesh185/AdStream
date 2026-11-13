from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass(frozen=True)
class ValidationContext:
    """Everything a validation run needs from outside the event: the clock and two policies."""

    now: datetime
    supported_currencies: frozenset[str]
    max_clock_skew: timedelta

    def __post_init__(self) -> None:
        if self.now.tzinfo is None or self.now.utcoffset() != timedelta(0):
            raise ValueError("now must be a timezone-aware UTC datetime")
