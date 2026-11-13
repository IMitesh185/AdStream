import re
from datetime import datetime, timedelta
from typing import Annotated, Literal

from pydantic import (
    AfterValidator,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    StrictInt,
    StrictStr,
    StringConstraints,
    ValidationInfo,
)

from .context import ValidationContext
from .errors import ReasonCode, custom_error

INT64_MIN = -(2**63)
INT64_MAX = 2**63 - 1

_UTC_TIMESTAMP = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,6})?Z", re.ASCII)


class ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


def _not_blank(value: str) -> str:
    if not value.strip():
        raise custom_error(ReasonCode.MISSING_FIELD, "Must not be empty or blank")
    return value


def _parse_utc(value: object) -> datetime:
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() != timedelta(0):
            raise custom_error(ReasonCode.INVALID_TIMESTAMP, "Timestamp must be UTC")
        return value
    if not isinstance(value, str):
        raise custom_error(ReasonCode.INVALID_TYPE, "Timestamp must be a string")
    if not _UTC_TIMESTAMP.fullmatch(value):
        raise custom_error(
            ReasonCode.INVALID_TIMESTAMP,
            "Timestamp must be RFC 3339 UTC ending in Z, with up to 6 fractional digits",
        )
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        raise custom_error(ReasonCode.INVALID_TIMESTAMP, "Timestamp is not a real date and time") from None


# The two checks below need the clock or a policy, which arrive through the validation context.
# Without a context (a model used on its own) only the shape of the value is checked.
def _not_in_future(value: datetime, info: ValidationInfo) -> datetime:
    context = info.context
    if isinstance(context, ValidationContext) and value > context.now + context.max_clock_skew:
        raise custom_error(ReasonCode.CLOCK_SKEW, "Timestamp is later than now plus the allowed clock skew")
    return value


def _supported_currency(value: str, info: ValidationInfo) -> str:
    context = info.context
    if isinstance(context, ValidationContext) and value not in context.supported_currencies:
        raise custom_error(ReasonCode.UNSUPPORTED_CURRENCY, "Currency {currency} is not supported", currency=value)
    return value


Id = Annotated[StrictStr, AfterValidator(_not_blank)]
Int64 = Annotated[StrictInt, Field(ge=INT64_MIN, le=INT64_MAX)]
PositiveInt64 = Annotated[StrictInt, Field(gt=0, le=INT64_MAX)]
Currency = Annotated[
    str,
    StringConstraints(strict=True, pattern=r"^[A-Z]{3}$"),
    AfterValidator(_supported_currency),
]
CountryCode = Annotated[str, StringConstraints(strict=True, pattern=r"^[A-Z]{2}$")]
# Literal rather than Enum: a strict Enum field rejects plain strings.
DeviceType = Literal["desktop", "mobile", "tablet", "connected_tv", "other"]
UtcTimestamp = Annotated[datetime, BeforeValidator(_parse_utc)]
EventTime = Annotated[UtcTimestamp, AfterValidator(_not_in_future)]


class Money(ContractModel):
    amount_micros: Int64
    currency: Currency


class NonNegativeMoney(Money):
    amount_micros: Annotated[Int64, Field(ge=0)]


class PositiveMoney(Money):
    amount_micros: Annotated[Int64, Field(gt=0)]
