from datetime import datetime, timedelta, timezone

import pytest
from pydantic import TypeAdapter, ValidationError

from adstream.contracts.context import ValidationContext
from adstream.contracts.primitives import (
    Currency,
    EventTime,
    Id,
    Money,
    NonNegativeMoney,
    PositiveMoney,
    UtcTimestamp,
)

from .builders import CONTEXT, NOW


def error_types(exc: pytest.ExceptionInfo[ValidationError]) -> list[str]:
    return [error["type"] for error in exc.value.errors()]


def test_money_accepts_integer_micros():
    assert Money(amount_micros=1_250_000, currency="INR").amount_micros == 1_250_000


@pytest.mark.parametrize("amount", [5.5, 5.0, "5", True, None, 2**63, -(2**63) - 1])
def test_money_rejects_anything_but_an_int64(amount):
    with pytest.raises(ValidationError):
        Money(amount_micros=amount, currency="INR")


def test_money_keeps_both_ends_of_int64():
    assert Money(amount_micros=2**63 - 1, currency="INR").amount_micros == 2**63 - 1
    assert Money(amount_micros=-(2**63), currency="INR").amount_micros == -(2**63)


def test_sign_rules_belong_to_the_field_not_to_money_itself():
    assert Money(amount_micros=-5, currency="INR").amount_micros == -5
    assert NonNegativeMoney(amount_micros=0, currency="INR").amount_micros == 0
    assert PositiveMoney(amount_micros=1, currency="INR").amount_micros == 1
    with pytest.raises(ValidationError):
        NonNegativeMoney(amount_micros=-1, currency="INR")
    with pytest.raises(ValidationError):
        PositiveMoney(amount_micros=0, currency="INR")


@pytest.mark.parametrize("code", ["inr", "Inr", "INRX", "IN", "", "1NR", 5, None])
def test_currency_must_be_three_uppercase_letters(code):
    with pytest.raises(ValidationError):
        TypeAdapter(Currency).validate_python(code)


def test_currency_policy_comes_from_the_context():
    adapter = TypeAdapter(Currency)
    assert adapter.validate_python("ABC") == "ABC"
    assert adapter.validate_python("INR", context=CONTEXT) == "INR"
    with pytest.raises(ValidationError) as exc:
        adapter.validate_python("ABC", context=CONTEXT)
    assert error_types(exc) == ["UNSUPPORTED_CURRENCY"]


@pytest.mark.parametrize(
    "value",
    ["2026-11-13T07:30:01Z", "2026-11-13T07:30:01.5Z", "2026-11-13T07:30:01.123456Z", NOW],
)
def test_timestamp_accepts_utc(value):
    assert TypeAdapter(UtcTimestamp).validate_python(value).utcoffset() == timedelta(0)


@pytest.mark.parametrize(
    "value",
    [
        "2026-11-13T07:30:01+00:00",
        "2026-11-13T07:30:01+05:30",
        "2026-11-13T07:30:01",
        "2026-11-13 07:30:01Z",
        "2026-11-13T07:30:01.1234567Z",
        "2026-13-13T07:30:01Z",
        "2026-02-30T00:00:00Z",
        1763019001,
        None,
        datetime(2026, 11, 13, 7, 30),
        datetime(2026, 11, 13, 7, 30, tzinfo=timezone(timedelta(hours=5, minutes=30))),
    ],
)
def test_timestamp_rejects_everything_else(value):
    with pytest.raises(ValidationError):
        TypeAdapter(UtcTimestamp).validate_python(value)


def test_event_time_may_be_old_but_not_far_in_the_future():
    adapter = TypeAdapter(EventTime)
    assert adapter.validate_python("2020-01-01T00:00:00Z", context=CONTEXT)
    assert adapter.validate_python("2026-11-13T07:39:00Z", context=CONTEXT)
    with pytest.raises(ValidationError) as exc:
        adapter.validate_python("2026-11-13T07:41:00Z", context=CONTEXT)
    assert error_types(exc) == ["CLOCK_SKEW"]


@pytest.mark.parametrize("value", ["", " ", "\t\n"])
def test_id_rejects_blank_strings(value):
    with pytest.raises(ValidationError) as exc:
        TypeAdapter(Id).validate_python(value)
    assert error_types(exc) == ["MISSING_FIELD"]


@pytest.mark.parametrize("value", [5, True, None, ["a"]])
def test_id_rejects_non_strings(value):
    with pytest.raises(ValidationError):
        TypeAdapter(Id).validate_python(value)


def test_id_is_kept_exactly_as_sent():
    assert TypeAdapter(Id).validate_python(" abc ") == " abc "


def test_context_requires_a_utc_clock():
    with pytest.raises(ValueError):
        ValidationContext(now=datetime(2026, 11, 13), supported_currencies=frozenset(), max_clock_skew=timedelta())
