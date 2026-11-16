"""
Canonical AdStream entity and event contracts (Pydantic v2).

Supports multi-ecosystem ad events with strict numeric validation (guarding
against Python's bool-is-int quirk), multi-currency normalization to USD micros,
schema evolution (v1/v2), and raw payload preservation.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Annotated, Any, Literal, Union
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictInt, field_validator, model_validator


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class SourceSystem(str, Enum):
    GOOGLE_ADS = "google_ads"
    YOUTUBE_ADS = "youtube_ads"
    AMAZON_ADS = "amazon_ads"
    META_ADS = "meta_ads"
    RETAIL_MEDIA = "retail_media"
    PROGRAMMATIC = "programmatic"
    SYNTHETIC = "synthetic"


class CampaignStatus(str, Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    EXHAUSTED = "EXHAUSTED"
    ENDED = "ENDED"


class PricingModel(str, Enum):
    CPM = "CPM"
    CPC = "CPC"
    CPA = "CPA"
    CPV = "CPV"


class CurrencyCode(str, Enum):
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    INR = "INR"
    JPY = "JPY"


# Deterministic reference FX rates to USD (used for normalized reporting; source currency preserved)
FX_TO_USD_SCALE_1E6: dict[CurrencyCode, int] = {
    CurrencyCode.USD: 1_000_000,
    CurrencyCode.EUR: 1_080_000,
    CurrencyCode.GBP: 1_270_000,
    CurrencyCode.INR: 12_000,
    CurrencyCode.JPY: 6_600,
}


def convert_to_usd_micros(amount_micros: int, currency: CurrencyCode) -> int:
    rate = FX_TO_USD_SCALE_1E6[currency]
    return (amount_micros * rate) // 1_000_000


class EventType(str, Enum):
    AD_REQUEST = "ad_request"
    BID = "bid"
    AUCTION_OUTCOME = "auction_outcome"
    IMPRESSION = "impression"
    CLICK = "click"
    VIDEO_INTERACTION = "video_interaction"
    CONVERSION = "conversion"
    INVALID_TRAFFIC = "invalid_traffic"
    BUDGET = "budget"
    BILLING_ADJUSTMENT = "billing_adjustment"


class VideoQuartile(str, Enum):
    START = "start"
    FIRST_QUARTILE = "q1"
    MIDPOINT = "q2"
    THIRD_QUARTILE = "q3"
    COMPLETE = "complete"


class ConversionAction(str, Enum):
    ADD_TO_CART = "add_to_cart"
    PURCHASE = "purchase"
    SIGNUP = "signup"


class LedgerEntryType(str, Enum):
    RESERVE = "RESERVE"
    CHARGE = "CHARGE"
    RELEASE = "RELEASE"
    PUBLISHER_PAYOUT = "PUBLISHER_PAYOUT"
    REFUND = "REFUND"
    ADJUSTMENT = "ADJUSTMENT"


NonNegativeMicros = Annotated[StrictInt, Field(ge=0)]
SignedMicros = StrictInt


# ---------------------------------------------------------------------------
# Entity Models
# ---------------------------------------------------------------------------


class Agency(BaseModel):
    model_config = ConfigDict(frozen=True)
    agency_id: str = Field(min_length=1)
    name: str = Field(min_length=1)


class Advertiser(BaseModel):
    model_config = ConfigDict(frozen=True)
    advertiser_id: str = Field(min_length=1)
    agency_id: str | None = None
    name: str = Field(min_length=1)
    tier: Literal["enterprise", "mid_market", "smb"] = "smb"
    country: str = Field(min_length=2, max_length=3)
    currency: CurrencyCode = CurrencyCode.USD


class Account(BaseModel):
    model_config = ConfigDict(frozen=True)
    account_id: str = Field(min_length=1)
    advertiser_id: str = Field(min_length=1)
    billing_currency: CurrencyCode = CurrencyCode.USD


class Campaign(BaseModel):
    campaign_id: str = Field(min_length=1)
    advertiser_id: str = Field(min_length=1)
    account_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    status: CampaignStatus = CampaignStatus.ACTIVE
    pricing_model: PricingModel = PricingModel.CPC
    daily_budget_micros: NonNegativeMicros
    remaining_budget_micros: NonNegativeMicros
    max_bid_micros: NonNegativeMicros
    currency: CurrencyCode = CurrencyCode.USD
    country_tier: str = "tier_1"
    version: StrictInt = 1

    @model_validator(mode="after")
    def _validate_budget_invariant(self) -> "Campaign":
        if self.remaining_budget_micros > self.daily_budget_micros:
            raise ValueError("remaining_budget_micros cannot exceed daily_budget_micros")
        return self


class AdGroup(BaseModel):
    model_config = ConfigDict(frozen=True)
    ad_group_id: str = Field(min_length=1)
    campaign_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    audience_segment: str | None = None


class CreativeAsset(BaseModel):
    model_config = ConfigDict(frozen=True)
    creative_id: str = Field(min_length=1)
    creative_format: Literal["banner", "native", "video", "sponsored_product"]
    duration_seconds: StrictInt | None = None


class Advertisement(BaseModel):
    model_config = ConfigDict(frozen=True)
    ad_id: str = Field(min_length=1)
    ad_group_id: str = Field(min_length=1)
    campaign_id: str = Field(min_length=1)
    creative_id: str = Field(min_length=1)
    product_id: str | None = None


class Product(BaseModel):
    model_config = ConfigDict(frozen=True)
    product_id: str = Field(min_length=1)
    advertiser_id: str = Field(min_length=1)
    category: str = Field(min_length=1)
    unit_price_micros: NonNegativeMicros


class Publisher(BaseModel):
    model_config = ConfigDict(frozen=True)
    publisher_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    platform_type: Literal["web", "mobile_app", "ctv", "retail_site", "search"]
    rev_share_bps: StrictInt = Field(default=7000, ge=0, le=10_000)


class Placement(BaseModel):
    model_config = ConfigDict(frozen=True)
    placement_id: str = Field(min_length=1)
    publisher_id: str = Field(min_length=1)
    channel: Literal["display", "video", "search", "sponsored_listing"]
    country: str = Field(min_length=2, max_length=3)


class AudienceSegment(BaseModel):
    model_config = ConfigDict(frozen=True)
    segment_id: str = Field(min_length=1)
    label: str = Field(min_length=1)


# ---------------------------------------------------------------------------
# Canonical Event Contracts (shared envelope + event-specific payloads)
# ---------------------------------------------------------------------------


class BaseAdEvent(BaseModel):
    """Shared canonical envelope across all advertising event families."""

    model_config = ConfigDict(extra="forbid")

    event_id: str = Field(min_length=1)
    idempotency_key: str = Field(min_length=1)
    event_type: EventType
    schema_version: StrictInt = Field(default=1, ge=1)
    source_system: SourceSystem
    source_event_id: str = Field(min_length=1)

    event_time: datetime
    ingested_at: datetime = Field(default_factory=utc_now)

    advertiser_id: str = Field(min_length=1)
    campaign_id: str = Field(min_length=1)
    ad_group_id: str | None = None
    ad_id: str | None = None
    creative_id: str | None = None
    publisher_id: str | None = None
    placement_id: str | None = None
    product_id: str | None = None

    user_pseudo_id: str | None = None
    audience_segment: str | None = None
    country: str = Field(min_length=2, max_length=3)
    region: str | None = None
    device_type: Literal["mobile", "desktop", "tablet", "ctv", "unknown"] = "unknown"
    browser: str | None = None
    currency: CurrencyCode = CurrencyCode.USD

    # v2 additive optional fields (backward-compatible schema evolution)
    creative_format: str | None = None
    trace_id: str | None = None

    # Arbitrary nested source attributes & raw payload preservation
    attributes: dict[str, Any] = Field(default_factory=dict)
    raw_payload: dict[str, Any] = Field(default_factory=dict)

    @field_validator("country")
    @classmethod
    def _uppercase_country(cls, v: str) -> str:
        clean = v.strip().upper()
        if not clean.isalpha():
            raise ValueError("country must be alphabetic ISO code")
        return clean

    @field_validator("event_time", "ingested_at")
    @classmethod
    def _ensure_tz_aware(cls, dt: datetime) -> datetime:
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)


class AdRequestEvent(BaseAdEvent):
    event_type: Literal[EventType.AD_REQUEST] = EventType.AD_REQUEST
    floor_price_micros: NonNegativeMicros = 0


class BidEvent(BaseAdEvent):
    event_type: Literal[EventType.BID] = EventType.BID
    request_id: str = Field(min_length=1)
    bid_price_micros: NonNegativeMicros


class AuctionOutcomeEvent(BaseAdEvent):
    event_type: Literal[EventType.AUCTION_OUTCOME] = EventType.AUCTION_OUTCOME
    request_id: str = Field(min_length=1)
    won: StrictBool
    clearing_price_micros: NonNegativeMicros = 0


class ImpressionEvent(BaseAdEvent):
    event_type: Literal[EventType.IMPRESSION] = EventType.IMPRESSION
    cost_micros: NonNegativeMicros
    viewable: StrictBool = True
    is_billable: StrictBool = True


class ClickEvent(BaseAdEvent):
    event_type: Literal[EventType.CLICK] = EventType.CLICK
    impression_id: str | None = None
    cost_micros: NonNegativeMicros
    is_billable: StrictBool = True
    user_ip_hash: str | None = None
    user_agent: str | None = None


class VideoInteractionEvent(BaseAdEvent):
    event_type: Literal[EventType.VIDEO_INTERACTION] = EventType.VIDEO_INTERACTION
    impression_id: str | None = None
    quartile: VideoQuartile
    cost_micros: NonNegativeMicros = 0
    is_billable: StrictBool = False


class ConversionEvent(BaseAdEvent):
    event_type: Literal[EventType.CONVERSION] = EventType.CONVERSION
    click_id: str | None = None
    impression_id: str | None = None
    action: ConversionAction
    revenue_micros: NonNegativeMicros
    cost_micros: NonNegativeMicros = 0
    is_billable: StrictBool = False


class InvalidTrafficEvent(BaseAdEvent):
    event_type: Literal[EventType.INVALID_TRAFFIC] = EventType.INVALID_TRAFFIC
    suspect_event_id: str = Field(min_length=1)
    reason_code: str = Field(min_length=1)
    blocked_cost_micros: NonNegativeMicros = 0


class BudgetEvent(BaseAdEvent):
    event_type: Literal[EventType.BUDGET] = EventType.BUDGET
    delta_micros: SignedMicros
    remaining_budget_micros: NonNegativeMicros


class BillingAdjustmentEvent(BaseAdEvent):
    event_type: Literal[EventType.BILLING_ADJUSTMENT] = EventType.BILLING_ADJUSTMENT
    reference_event_id: str = Field(min_length=1)
    adjustment_micros: SignedMicros
    reason: str = Field(min_length=1)


CanonicalAdEvent = Union[
    AdRequestEvent,
    BidEvent,
    AuctionOutcomeEvent,
    ImpressionEvent,
    ClickEvent,
    VideoInteractionEvent,
    ConversionEvent,
    InvalidTrafficEvent,
    BudgetEvent,
    BillingAdjustmentEvent,
]


class QuarantineRecord(BaseModel):
    """Quarantined raw event with failure context for replay/auditability."""

    quarantine_id: str = Field(default_factory=lambda: f"quar_{uuid4().hex[:16]}")
    source_system: str
    reason_code: str
    error_detail: str
    raw_payload: Any
    quarantined_at: datetime = Field(default_factory=utc_now)


class LedgerEntry(BaseModel):
    """Immutable financial ledger row protecting campaign & publisher balances."""

    entry_id: str = Field(default_factory=lambda: f"led_{uuid4().hex[:16]}")
    idempotency_key: str = Field(min_length=1)
    event_id: str = Field(min_length=1)
    campaign_id: str = Field(min_length=1)
    advertiser_id: str = Field(min_length=1)
    publisher_id: str | None = None
    entry_type: LedgerEntryType
    amount_micros: SignedMicros
    balance_after_micros: NonNegativeMicros
    currency: CurrencyCode = CurrencyCode.USD
    usd_equivalent_micros: SignedMicros
    created_at: datetime = Field(default_factory=utc_now)
