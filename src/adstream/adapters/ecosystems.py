"""Concrete ecosystem adapters preserving original payloads and source identifiers."""

from __future__ import annotations

from typing import Any

from adstream.adapters.base import AdapterRegistry, build_canonical_event
from adstream.domain.exceptions import InvalidEventError
from adstream.domain.models import CanonicalAdEvent, SourceSystem


def _require_str(raw: dict[str, Any], key: str) -> str:
    val = raw.get(key)
    if not isinstance(val, str) or not val.strip():
        raise InvalidEventError(f"Missing or invalid string field '{key}'")
    return val


class CanonicalPassthroughAdapter:
    """Adapter for AdStream native / synthetic payloads already using canonical keys."""

    source_system = SourceSystem.SYNTHETIC

    def to_canonical(self, raw: dict[str, Any]) -> CanonicalAdEvent:
        if not isinstance(raw, dict):
            raise InvalidEventError("Payload must be a JSON object")
        normalized = {
            **raw,
            "source_system": raw.get("source_system", SourceSystem.SYNTHETIC.value),
            "source_event_id": raw.get("source_event_id") or raw.get("event_id"),
            "idempotency_key": raw.get("idempotency_key") or raw.get("event_id"),
        }
        return build_canonical_event(normalized, raw_payload=raw)


class GoogleAdsAdapter:
    """Normalizes Google Ads style payloads (gclid, costMicros, campaignId, geoCountry)."""

    source_system = SourceSystem.GOOGLE_ADS

    def to_canonical(self, raw: dict[str, Any]) -> CanonicalAdEvent:
        source_id = _require_str(raw, "googleEventId")
        event_type = _require_str(raw, "kind")
        normalized: dict[str, Any] = {
            "event_id": f"gads_{source_id}",
            "idempotency_key": raw.get("idempotencyKey") or f"gads_{source_id}",
            "event_type": event_type,
            "schema_version": raw.get("schemaVersion", 1),
            "source_system": SourceSystem.GOOGLE_ADS.value,
            "source_event_id": source_id,
            "event_time": raw.get("timestampUtc"),
            "advertiser_id": raw.get("customerId"),
            "campaign_id": raw.get("campaignId"),
            "ad_group_id": raw.get("adGroupId"),
            "ad_id": raw.get("adId"),
            "publisher_id": raw.get("publisherId"),
            "placement_id": raw.get("placementId"),
            "country": raw.get("geoCountry"),
            "device_type": raw.get("device", "unknown"),
            "currency": raw.get("currencyCode", "USD"),
            "creative_format": raw.get("creativeFormat"),
            "attributes": {"gclid": raw.get("gclid"), **(raw.get("extensions") or {})},
        }
        if event_type in ("impression", "click"):
            normalized["cost_micros"] = raw.get("costMicros", 0)
        if event_type == "click":
            normalized["impression_id"] = raw.get("impressionId")
            normalized["user_ip_hash"] = raw.get("ipHash")
        if event_type == "conversion":
            normalized["click_id"] = raw.get("clickId")
            normalized["action"] = raw.get("conversionAction", "purchase")
            normalized["revenue_micros"] = raw.get("conversionValueMicros", 0)
        return build_canonical_event(normalized, raw_payload=raw)


class YouTubeAdsAdapter:
    """Normalizes YouTube video ad events (videoQuartile, cpvMicros, channelPublisherId)."""

    source_system = SourceSystem.YOUTUBE_ADS

    def to_canonical(self, raw: dict[str, Any]) -> CanonicalAdEvent:
        source_id = _require_str(raw, "ytEventId")
        event_type = raw.get("eventType", "video_interaction")
        normalized: dict[str, Any] = {
            "event_id": f"yt_{source_id}",
            "idempotency_key": raw.get("idempotencyKey") or f"yt_{source_id}",
            "event_type": event_type,
            "schema_version": raw.get("schemaVersion", 1),
            "source_system": SourceSystem.YOUTUBE_ADS.value,
            "source_event_id": source_id,
            "event_time": raw.get("occurredAt"),
            "advertiser_id": raw.get("advertiserId"),
            "campaign_id": raw.get("campaignId"),
            "ad_id": raw.get("videoAdId"),
            "creative_id": raw.get("creativeId"),
            "publisher_id": raw.get("channelPublisherId", "pub_youtube"),
            "placement_id": raw.get("placementId"),
            "country": raw.get("country"),
            "device_type": raw.get("deviceType", "ctv"),
            "currency": raw.get("currency", "USD"),
            "creative_format": "video",
            "attributes": {"video_id": raw.get("videoId"), "skip_offset_sec": raw.get("skipOffsetSec")},
        }
        if event_type == "video_interaction":
            normalized["quartile"] = raw.get("videoQuartile")
            normalized["impression_id"] = raw.get("impressionId")
            normalized["cost_micros"] = raw.get("cpvMicros", 0)
            normalized["is_billable"] = raw.get("cpvMicros", 0) > 0
        elif event_type in ("impression", "click"):
            normalized["cost_micros"] = raw.get("costMicros", 0)
        return build_canonical_event(normalized, raw_payload=raw)


class AmazonAdsAdapter:
    """Normalizes Amazon Sponsored Ads payloads (asin, sku, spendsMicros)."""

    source_system = SourceSystem.AMAZON_ADS

    def to_canonical(self, raw: dict[str, Any]) -> CanonicalAdEvent:
        source_id = _require_str(raw, "amznEventId")
        event_type = _require_str(raw, "eventType")
        normalized: dict[str, Any] = {
            "event_id": f"amzn_{source_id}",
            "idempotency_key": raw.get("idempotencyKey") or f"amzn_{source_id}",
            "event_type": event_type,
            "schema_version": raw.get("schemaVersion", 1),
            "source_system": SourceSystem.AMAZON_ADS.value,
            "source_event_id": source_id,
            "event_time": raw.get("eventTimestamp"),
            "advertiser_id": raw.get("sellerAccountId"),
            "campaign_id": raw.get("campaignId"),
            "ad_group_id": raw.get("adGroupId"),
            "product_id": raw.get("asin"),
            "publisher_id": raw.get("marketplacePublisherId", "pub_amazon_retail"),
            "country": raw.get("marketplaceCountry"),
            "device_type": raw.get("device", "desktop"),
            "currency": raw.get("currency", "USD"),
            "attributes": {"asin": raw.get("asin"), "keyword": raw.get("searchTerm")},
        }
        if event_type in ("impression", "click"):
            normalized["cost_micros"] = raw.get("spendsMicros", 0)
        if event_type == "conversion":
            normalized["click_id"] = raw.get("clickId")
            normalized["action"] = raw.get("action", "purchase")
            normalized["revenue_micros"] = raw.get("attributedSalesMicros", 0)
        return build_canonical_event(normalized, raw_payload=raw)


class MetaAdsAdapter:
    """Normalizes Meta Ads payloads (fbEventId, adsetId, spendMicros)."""

    source_system = SourceSystem.META_ADS

    def to_canonical(self, raw: dict[str, Any]) -> CanonicalAdEvent:
        source_id = _require_str(raw, "fbEventId")
        event_type = _require_str(raw, "eventName")
        normalized: dict[str, Any] = {
            "event_id": f"meta_{source_id}",
            "idempotency_key": raw.get("idempotencyKey") or f"meta_{source_id}",
            "event_type": event_type,
            "schema_version": raw.get("schemaVersion", 1),
            "source_system": SourceSystem.META_ADS.value,
            "source_event_id": source_id,
            "event_time": raw.get("eventTime"),
            "advertiser_id": raw.get("adAccountId"),
            "campaign_id": raw.get("campaignId"),
            "ad_group_id": raw.get("adsetId"),
            "ad_id": raw.get("adId"),
            "publisher_id": raw.get("surface", "pub_meta_feed"),
            "country": raw.get("country"),
            "device_type": raw.get("platformDevice", "mobile"),
            "currency": raw.get("currency", "USD"),
            "attributes": {"fbp": raw.get("fbp"), "placement_surface": raw.get("surface")},
        }
        if event_type in ("impression", "click"):
            normalized["cost_micros"] = raw.get("spendMicros", 0)
        if event_type == "conversion":
            normalized["click_id"] = raw.get("clickId")
            normalized["action"] = raw.get("action", "purchase")
            normalized["revenue_micros"] = raw.get("valueMicros", 0)
        return build_canonical_event(normalized, raw_payload=raw)


class RetailMediaAdapter:
    """Normalizes Retail Media Network payloads."""

    source_system = SourceSystem.RETAIL_MEDIA

    def to_canonical(self, raw: dict[str, Any]) -> CanonicalAdEvent:
        source_id = _require_str(raw, "rmnEventId")
        event_type = _require_str(raw, "eventType")
        normalized: dict[str, Any] = {
            "event_id": f"rmn_{source_id}",
            "idempotency_key": raw.get("idempotencyKey") or f"rmn_{source_id}",
            "event_type": event_type,
            "schema_version": raw.get("schemaVersion", 1),
            "source_system": SourceSystem.RETAIL_MEDIA.value,
            "source_event_id": source_id,
            "event_time": raw.get("timestamp"),
            "advertiser_id": raw.get("brandId"),
            "campaign_id": raw.get("campaignId"),
            "product_id": raw.get("skuId"),
            "publisher_id": raw.get("retailerId"),
            "placement_id": raw.get("placementSlot"),
            "country": raw.get("country"),
            "device_type": raw.get("device", "mobile"),
            "currency": raw.get("currency", "USD"),
            "attributes": {"store_id": raw.get("storeId"), "sku_id": raw.get("skuId")},
        }
        if event_type in ("impression", "click"):
            normalized["cost_micros"] = raw.get("chargeMicros", 0)
        if event_type == "conversion":
            normalized["click_id"] = raw.get("clickId")
            normalized["action"] = raw.get("action", "purchase")
            normalized["revenue_micros"] = raw.get("basketMicros", 0)
        return build_canonical_event(normalized, raw_payload=raw)


class ProgrammaticAdapter:
    """Normalizes OpenRTB-like programmatic exchange payloads."""

    source_system = SourceSystem.PROGRAMMATIC

    def to_canonical(self, raw: dict[str, Any]) -> CanonicalAdEvent:
        source_id = _require_str(raw, "exchangeEventId")
        event_type = _require_str(raw, "eventType")
        normalized: dict[str, Any] = {
            "event_id": f"rtb_{source_id}",
            "idempotency_key": raw.get("idempotencyKey") or f"rtb_{source_id}",
            "event_type": event_type,
            "schema_version": raw.get("schemaVersion", 1),
            "source_system": SourceSystem.PROGRAMMATIC.value,
            "source_event_id": source_id,
            "event_time": raw.get("ts"),
            "advertiser_id": raw.get("seatId"),
            "campaign_id": raw.get("campaignId"),
            "publisher_id": raw.get("sspPublisherId"),
            "placement_id": raw.get("tagId"),
            "country": raw.get("country"),
            "device_type": raw.get("deviceType", "desktop"),
            "currency": raw.get("cur", "USD"),
            "attributes": {"auction_id": raw.get("auctionId"), "deal_id": raw.get("dealId")},
        }
        if event_type in ("impression", "click"):
            normalized["cost_micros"] = raw.get("clearingMicros", 0)
        elif event_type == "bid":
            normalized["request_id"] = raw.get("requestId")
            normalized["bid_price_micros"] = raw.get("bidMicros", 0)
        elif event_type == "auction_outcome":
            normalized["request_id"] = raw.get("requestId")
            normalized["won"] = raw.get("won", False)
            normalized["clearing_price_micros"] = raw.get("clearingMicros", 0)
        return build_canonical_event(normalized, raw_payload=raw)


def create_default_registry() -> AdapterRegistry:
    """Build an AdapterRegistry preloaded with all supported ecosystem adapters."""
    registry = AdapterRegistry()
    for adapter in (
        CanonicalPassthroughAdapter(),
        GoogleAdsAdapter(),
        YouTubeAdsAdapter(),
        AmazonAdsAdapter(),
        MetaAdsAdapter(),
        RetailMediaAdapter(),
        ProgrammaticAdapter(),
    ):
        registry.register(adapter)
    return registry
