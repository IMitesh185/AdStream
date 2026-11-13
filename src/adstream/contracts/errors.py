from enum import StrEnum
from typing import NoReturn

from pydantic import BaseModel, ConfigDict, ValidationError
from pydantic_core import InitErrorDetails, PydanticCustomError


class ReasonCode(StrEnum):
    MALFORMED_JSON = "MALFORMED_JSON"
    UNKNOWN_EVENT_TYPE = "UNKNOWN_EVENT_TYPE"
    UNSUPPORTED_SCHEMA = "UNSUPPORTED_SCHEMA"
    MISSING_FIELD = "MISSING_FIELD"
    INVALID_TYPE = "INVALID_TYPE"
    INVALID_VALUE = "INVALID_VALUE"
    OUT_OF_RANGE = "OUT_OF_RANGE"
    UNDECLARED_FIELD = "UNDECLARED_FIELD"
    INVALID_TIMESTAMP = "INVALID_TIMESTAMP"
    CLOCK_SKEW = "CLOCK_SKEW"
    UNSUPPORTED_CURRENCY = "UNSUPPORTED_CURRENCY"


class ValidationIssue(BaseModel):
    model_config = ConfigDict(frozen=True)

    code: ReasonCode
    field_path: str
    message: str


def custom_error(code: ReasonCode, message: str, **context: str) -> PydanticCustomError:
    """An error whose Pydantic `type` is our reason code, so it passes through unchanged."""
    return PydanticCustomError(code.value, message, context or None)


def reject(*problems: tuple[ReasonCode, str, str]) -> NoReturn:
    """Raise several located errors at once. Each problem is (code, field name, message)."""
    raise ValidationError.from_exception_data(
        "contract",
        [
            InitErrorDetails(type=custom_error(code, message), loc=(field,), input=None)
            for code, field, message in problems
        ],
    )
