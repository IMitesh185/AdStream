from datetime import datetime, timedelta, timezone
from typing import Any

from adstream.contracts.context import ValidationContext

NOW = datetime(2026, 11, 13, 7, 35, 0, tzinfo=timezone.utc)
CONTEXT = ValidationContext(
    now=NOW,
    supported_currencies=frozenset({"INR", "USD"}),
    max_clock_skew=timedelta(minutes=5),
)


def _envelope(event_type: str, payload: dict[str, Any], occurred_at: str) -> dict[str, Any]:
    return {
        "event_id": f"evt-{event_type}-1",
        "event_type": event_type,
        "schema_version": 1,
        "source": "synthetic.retail.account_demo",
        "source_event_id": f"source-{event_type}-1",
        "occurred_at": occurred_at,
        "payload": payload,
        "extensions": {},
    }


def _placement() -> dict[str, Any]:
    return {
        "request_id": "request-1",
        "advertiser_id": "advertiser-demo",
        "campaign_id": "campaign-demo",
        "ad_id": "ad-demo",
        "publisher_id": "publisher-demo",
        "app_site_id": "site-demo",
        "placement_id": "placement-demo",
    }


def _identity() -> dict[str, Any]:
    return {
        "user_id": "user-demo",
        "identity_namespace": "synthetic.advertiser-demo",
        "country_code": "IN",
        "device_type": "mobile",
    }


def impression_event() -> dict[str, Any]:
    payload = {**_placement(), "impression_id": "impression-1"}
    return _envelope("impression", payload, "2026-11-13T07:30:00.000000Z")


def click_event() -> dict[str, Any]:
    payload = {
        **_placement(),
        **_identity(),
        "click_id": "click-1",
        "impression_id": "impression-1",
        "landing_page_ref": "destination-demo-v1",
    }
    return _envelope("click", payload, "2026-11-13T07:30:01.000000Z")


def purchase_event() -> dict[str, Any]:
    payload = {
        "request_id": "request-1",
        "conversion_id": "conversion-1",
        "advertiser_id": "advertiser-demo",
        "conversion_type": "purchase",
        "order_id": "order-demo-1",
        "revenue": {"amount_micros": 500_000_000, "currency": "INR"},
        **_identity(),
        "reported_click_id": "click-1",
        "items": [
            {
                "line_item_id": "line-1",
                "product_id": "product-demo",
                "quantity": 1,
                "revenue": {"amount_micros": 500_000_000, "currency": "INR"},
            }
        ],
    }
    return _envelope("conversion", payload, "2026-11-13T07:31:00.000000Z")


def add_to_cart_event() -> dict[str, Any]:
    event = purchase_event()
    payload = event["payload"]
    for key in ("order_id", "revenue", "items"):
        del payload[key]
    payload.update(conversion_type="add_to_cart", product_id="product-demo", quantity=2)
    return event


def custom_conversion_event() -> dict[str, Any]:
    event = purchase_event()
    payload = event["payload"]
    for key in ("order_id", "items"):
        del payload[key]
    payload.update(conversion_type="custom", action_name="newsletter_signup")
    return event
