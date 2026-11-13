import hashlib
import json
from collections.abc import Callable
from typing import Any, get_args

import pytest

from adstream.contracts import Accepted, Quarantined, ReasonCode, validate_event
from adstream.contracts.events import EVENT_TYPES, ClickEvent, ConversionEvent, ImpressionEvent

from .builders import (
    CONTEXT,
    NOW,
    add_to_cart_event,
    click_event,
    custom_conversion_event,
    impression_event,
    purchase_event,
)

R = ReasonCode
Mutation = Callable[[dict[str, Any]], object]


def submit(event: dict[str, Any], receipt_id: str = "receipt-1"):
    return validate_event(json.dumps(event).encode(), receipt_id=receipt_id, context=CONTEXT)


def found(outcome) -> set[tuple[ReasonCode, str]]:
    assert isinstance(outcome, Quarantined)
    return {(issue.code, issue.field_path) for issue in outcome.record.errors}


def _walk(event: dict[str, Any], keys: list[str]) -> Any:
    target: Any = event
    for key in keys:
        target = target[int(key)] if key.isdigit() else target[key]
    return target


def remove(path: str) -> Mutation:
    *parents, last = path.split("/")

    def mutate(event: dict[str, Any]) -> None:
        del _walk(event, parents)[last]

    return mutate


def replace(path: str, value: Any) -> Mutation:
    *parents, last = path.split("/")

    def mutate(event: dict[str, Any]) -> None:
        _walk(event, parents)[int(last) if last.isdigit() else last] = value

    return mutate


def add_duplicate_line_item(event: dict[str, Any]) -> None:
    items = event["payload"]["items"]
    items.append(dict(items[0]))


GOOD_EVENTS = [click_event, impression_event, purchase_event, add_to_cart_event, custom_conversion_event]


@pytest.mark.parametrize("build", GOOD_EVENTS, ids=lambda build: build.__name__)
def test_good_events_are_accepted(build):
    event = build()
    outcome = submit(event)
    assert isinstance(outcome, Accepted)
    assert outcome.event.event_id == event["event_id"]
    assert outcome.event.event_type == event["event_type"]


def test_an_anonymous_click_is_valid():
    event = click_event()
    del event["payload"]["user_id"]
    del event["payload"]["identity_namespace"]
    outcome = submit(event)
    assert isinstance(outcome, Accepted)
    assert outcome.event.payload.user_id is None


def test_zero_revenue_is_a_known_amount_not_a_missing_one():
    event = purchase_event()
    event["payload"]["revenue"]["amount_micros"] = 0
    event["payload"]["items"][0]["revenue"]["amount_micros"] = 0
    outcome = submit(event)
    assert isinstance(outcome, Accepted)
    assert outcome.event.payload.revenue.amount_micros == 0


@pytest.mark.parametrize("occurred_at", ["2020-01-01T00:00:00Z", "2026-11-13T07:39:00Z"])
def test_late_events_and_events_within_the_clock_skew_are_valid(occurred_at):
    event = click_event()
    event["occurred_at"] = occurred_at
    assert isinstance(submit(event), Accepted)


def test_ingestion_assigns_received_at_whatever_the_producer_sent():
    event = click_event()
    event["received_at"] = "2000-01-01T00:00:00Z"
    outcome = submit(event)
    assert isinstance(outcome, Accepted)
    assert outcome.event.received_at == NOW


def test_extensions_are_kept_as_sent():
    event = click_event()
    event["extensions"] = {"vendor": {"score": 0.7}}
    outcome = submit(event)
    assert isinstance(outcome, Accepted)
    assert outcome.event.extensions == {"vendor": {"score": 0.7}}


BROKEN = [
    pytest.param(click_event, remove("payload/ad_id"), R.MISSING_FIELD, "/payload/ad_id", id="click: missing ad_id"),
    pytest.param(click_event, replace("payload/ad_id", None), R.MISSING_FIELD, "/payload/ad_id", id="click: null ad_id"),
    pytest.param(click_event, replace("payload/ad_id", "   "), R.MISSING_FIELD, "/payload/ad_id", id="click: blank ad_id"),
    pytest.param(click_event, replace("payload/ad_id", 7), R.INVALID_TYPE, "/payload/ad_id", id="click: numeric ad_id"),
    pytest.param(click_event, remove("payload/impression_id"), R.MISSING_FIELD, "/payload/impression_id", id="click: missing impression_id"),
    pytest.param(click_event, remove("payload/identity_namespace"), R.MISSING_FIELD, "/payload/identity_namespace", id="click: user_id without namespace"),
    pytest.param(click_event, remove("payload/user_id"), R.MISSING_FIELD, "/payload/user_id", id="click: namespace without user_id"),
    pytest.param(click_event, replace("payload/clicked_at", "2026-11-13T07:30:01Z"), R.UNDECLARED_FIELD, "/payload/clicked_at", id="click: undeclared field"),
    pytest.param(click_event, replace("payload/device_type", "toaster"), R.INVALID_VALUE, "/payload/device_type", id="click: unknown device"),
    pytest.param(click_event, replace("payload/country_code", "in"), R.INVALID_VALUE, "/payload/country_code", id="click: lowercase country"),
    pytest.param(click_event, replace("payload/audience_ids", ["a", "a"]), R.INVALID_VALUE, "/payload/audience_ids", id="click: repeated audience"),
    pytest.param(impression_event, remove("payload/impression_id"), R.MISSING_FIELD, "/payload/impression_id", id="impression: missing impression_id"),
    pytest.param(click_event, replace("event_type", "refund"), R.UNKNOWN_EVENT_TYPE, "/event_type", id="envelope: unknown event type"),
    pytest.param(click_event, replace("event_type", "bid"), R.UNKNOWN_EVENT_TYPE, "/event_type", id="envelope: contract event not modelled yet"),
    pytest.param(click_event, remove("event_type"), R.MISSING_FIELD, "/event_type", id="envelope: missing event type"),
    pytest.param(click_event, replace("schema_version", 2), R.UNSUPPORTED_SCHEMA, "/schema_version", id="envelope: unsupported schema version"),
    pytest.param(click_event, replace("schema_version", "1"), R.INVALID_TYPE, "/schema_version", id="envelope: schema version as text"),
    pytest.param(click_event, replace("event_id", ""), R.MISSING_FIELD, "/event_id", id="envelope: empty event_id"),
    pytest.param(click_event, replace("source_event_id", 12), R.INVALID_TYPE, "/source_event_id", id="envelope: numeric source_event_id"),
    pytest.param(click_event, replace("occurred_at", "2026-11-13T13:00:01+05:30"), R.INVALID_TIMESTAMP, "/occurred_at", id="envelope: local time with offset"),
    pytest.param(click_event, replace("occurred_at", "2026-11-13T07:41:00Z"), R.CLOCK_SKEW, "/occurred_at", id="envelope: too far in the future"),
    pytest.param(click_event, replace("occurred_at", None), R.MISSING_FIELD, "/occurred_at", id="envelope: null occurred_at"),
    pytest.param(click_event, replace("extensions", None), R.MISSING_FIELD, "/extensions", id="envelope: null extensions"),
    pytest.param(click_event, replace("zzz", "x"), R.UNDECLARED_FIELD, "/zzz", id="envelope: undeclared field"),
    pytest.param(click_event, remove("payload"), R.MISSING_FIELD, "/payload", id="envelope: missing payload"),
    pytest.param(click_event, replace("payload", "oops"), R.INVALID_TYPE, "/payload", id="envelope: payload is not an object"),
    pytest.param(purchase_event, replace("payload/revenue/amount_micros", -1), R.OUT_OF_RANGE, "/payload/revenue/amount_micros", id="money: negative revenue"),
    pytest.param(purchase_event, replace("payload/revenue/amount_micros", 500.5), R.INVALID_TYPE, "/payload/revenue/amount_micros", id="money: fractional micros"),
    pytest.param(purchase_event, replace("payload/revenue/amount_micros", 500_000_000.0), R.INVALID_TYPE, "/payload/revenue/amount_micros", id="money: whole number written as a float"),
    pytest.param(purchase_event, replace("payload/revenue/amount_micros", True), R.INVALID_TYPE, "/payload/revenue/amount_micros", id="money: boolean micros"),
    pytest.param(purchase_event, replace("payload/revenue/amount_micros", 2**63), R.OUT_OF_RANGE, "/payload/revenue/amount_micros", id="money: beyond int64"),
    pytest.param(purchase_event, replace("payload/revenue/currency", "JPY"), R.UNSUPPORTED_CURRENCY, "/payload/revenue/currency", id="money: unsupported currency"),
    pytest.param(purchase_event, replace("payload/revenue/currency", "inr"), R.INVALID_VALUE, "/payload/revenue/currency", id="money: lowercase currency"),
    pytest.param(purchase_event, replace("payload/revenue", 5), R.INVALID_TYPE, "/payload/revenue", id="money: revenue is not an object"),
    pytest.param(purchase_event, remove("payload/order_id"), R.MISSING_FIELD, "/payload/order_id", id="purchase: missing order_id"),
    pytest.param(purchase_event, remove("payload/revenue"), R.MISSING_FIELD, "/payload/revenue", id="purchase: missing revenue"),
    pytest.param(add_to_cart_event, remove("payload/quantity"), R.MISSING_FIELD, "/payload/quantity", id="add_to_cart: missing quantity"),
    pytest.param(custom_conversion_event, remove("payload/action_name"), R.MISSING_FIELD, "/payload/action_name", id="custom: missing action_name"),
    pytest.param(purchase_event, replace("payload/conversion_type", "refund"), R.INVALID_VALUE, "/payload/conversion_type", id="conversion: unknown type"),
    pytest.param(purchase_event, replace("payload/reported_ad_id", "ad-demo"), R.MISSING_FIELD, "/payload/reported_campaign_id", id="conversion: reported ad without campaign"),
    pytest.param(purchase_event, replace("payload/items/0/quantity", 0), R.OUT_OF_RANGE, "/payload/items/0/quantity", id="items: zero quantity"),
    pytest.param(purchase_event, replace("payload/items/0/revenue/amount_micros", 1), R.INVALID_VALUE, "/payload/items", id="items: do not add up to the revenue"),
    pytest.param(purchase_event, replace("payload/items/0/revenue/currency", "USD"), R.INVALID_VALUE, "/payload/items", id="items: different currency"),
    pytest.param(purchase_event, add_duplicate_line_item, R.INVALID_VALUE, "/payload/items", id="items: repeated line_item_id"),
]


@pytest.mark.parametrize("build, mutate, code, path", BROKEN)
def test_one_broken_thing_is_quarantined_with_exactly_its_reason_and_location(build, mutate, code, path):
    event = build()
    mutate(event)
    assert found(submit(event)) == {(code, path)}


def test_every_problem_is_reported_not_just_the_first():
    event = click_event()
    event["event_id"] = ""
    del event["payload"]["ad_id"]
    event["payload"]["click_id"] = 5
    assert found(submit(event)) == {
        (R.MISSING_FIELD, "/event_id"),
        (R.MISSING_FIELD, "/payload/ad_id"),
        (R.INVALID_TYPE, "/payload/click_id"),
    }


def test_a_quarantine_record_keeps_the_evidence():
    event = click_event()
    del event["payload"]["ad_id"]
    raw = json.dumps(event).encode()
    outcome = validate_event(raw, receipt_id="receipt-7", context=CONTEXT)
    assert isinstance(outcome, Quarantined)
    record = outcome.record
    assert record.quarantine_id == "q-receipt-7"
    assert record.receipt_id == "receipt-7"
    assert record.stage == "schema"
    assert record.event_id == "evt-click-1"
    assert record.event_type == "click"
    assert record.observed_schema_version == "1"
    assert record.raw_payload_sha256 == hashlib.sha256(raw).hexdigest()
    assert record.raw_payload_ref == f"sha256:{record.raw_payload_sha256}"
    assert record.received_at == NOW
    assert record.quarantined_at == NOW


def test_an_untrustworthy_event_id_is_not_copied_into_the_record():
    event = click_event()
    event["event_id"] = "  "
    outcome = submit(event)
    assert isinstance(outcome, Quarantined)
    assert outcome.record.event_id is None


UNREADABLE = [
    pytest.param(b"", id="empty body"),
    pytest.param(b"not json", id="not json"),
    pytest.param(b'{"event_type": "click"', id="truncated"),
    pytest.param(b"\xff\xfe\x00", id="invalid utf-8"),
    pytest.param(b'{"a": 1, "a": 2}', id="repeated key"),
    pytest.param(b"NaN", id="NaN"),
    pytest.param(b'{"x": Infinity}', id="Infinity"),
    pytest.param(b"[" * 100_000, id="nesting too deep"),
    pytest.param(b"1" * 5000, id="absurdly long number"),
]


@pytest.mark.parametrize("raw", UNREADABLE)
def test_unreadable_bodies_are_quarantined_as_malformed_json(raw):
    outcome = validate_event(raw, receipt_id="receipt-1", context=CONTEXT)
    assert found(outcome) == {(R.MALFORMED_JSON, "")}
    assert outcome.record.event_id is None
    assert outcome.record.raw_payload_sha256 == hashlib.sha256(raw).hexdigest()


@pytest.mark.parametrize(
    "raw, code, path",
    [
        (b"[]", R.INVALID_TYPE, ""),
        (b"null", R.INVALID_TYPE, ""),
        (b'"text"', R.INVALID_TYPE, ""),
        (b"42", R.INVALID_TYPE, ""),
        (b"{}", R.MISSING_FIELD, "/event_type"),
    ],
)
def test_valid_json_that_is_not_an_event_is_quarantined(raw, code, path):
    outcome = validate_event(raw, receipt_id="receipt-1", context=CONTEXT)
    assert found(outcome) == {(code, path)}


def test_the_same_bytes_always_give_the_same_outcome():
    good = json.dumps(click_event()).encode()
    bad = b'{"event_type": "click"'
    for raw in (good, bad):
        first = validate_event(raw, receipt_id="receipt-1", context=CONTEXT)
        second = validate_event(raw, receipt_id="receipt-1", context=CONTEXT)
        assert first == second


def test_event_types_match_the_modelled_events():
    tags = {get_args(model.model_fields["event_type"].annotation)[0] for model in (ClickEvent, ImpressionEvent, ConversionEvent)}
    assert tags == EVENT_TYPES
