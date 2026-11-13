from typing import Annotated, Any, Literal, Self

from pydantic import AfterValidator, Field, StrictInt, TypeAdapter, field_validator, model_validator

from .errors import ReasonCode, custom_error, reject
from .primitives import (
    ContractModel,
    CountryCode,
    DeviceType,
    EventTime,
    Id,
    NonNegativeMoney,
    PositiveInt64,
    UtcTimestamp,
)

SUPPORTED_SCHEMA_VERSIONS = frozenset({1})


def _supported_schema_version(value: int) -> int:
    if value not in SUPPORTED_SCHEMA_VERSIONS:
        raise custom_error(
            ReasonCode.UNSUPPORTED_SCHEMA, "Schema version {version} is not supported", version=str(value)
        )
    return value


SchemaVersion = Annotated[StrictInt, AfterValidator(_supported_schema_version)]


class RequestRef(ContractModel):
    request_id: Id


class AdContext(ContractModel):
    advertiser_id: Id
    campaign_id: Id
    ad_id: Id


class InventoryContext(ContractModel):
    publisher_id: Id
    app_site_id: Id
    placement_id: Id


class ObservationContext(ContractModel):
    user_id: Id | None = None
    identity_namespace: Id | None = None
    country_code: CountryCode | None = None
    device_type: DeviceType | None = None
    audience_ids: list[Id] = Field(default_factory=list)

    @field_validator("audience_ids")
    @classmethod
    def _audience_ids_are_distinct(cls, value: list[str]) -> list[str]:
        if len(set(value)) != len(value):
            raise custom_error(ReasonCode.INVALID_VALUE, "Audience ids must be distinct")
        return value

    @model_validator(mode="after")
    def _user_and_namespace_go_together(self) -> Self:
        if self.user_id is not None and self.identity_namespace is None:
            reject((ReasonCode.MISSING_FIELD, "identity_namespace", "Required when user_id is present"))
        if self.identity_namespace is not None and self.user_id is None:
            reject((ReasonCode.MISSING_FIELD, "user_id", "Required when identity_namespace is present"))
        return self


class ClickPayload(RequestRef, AdContext, InventoryContext, ObservationContext):
    click_id: Id
    impression_id: Id
    landing_page_ref: Id | None = None


class ImpressionPayload(RequestRef, AdContext, InventoryContext, ObservationContext):
    impression_id: Id
    bid_id: Id | None = None
    result_id: Id | None = None


class ConversionItem(ContractModel):
    line_item_id: Id
    product_id: Id
    quantity: PositiveInt64
    revenue: NonNegativeMoney


_REQUIRED_BY_CONVERSION_TYPE = {
    "purchase": ("order_id", "revenue"),
    "add_to_cart": ("product_id", "quantity"),
    "custom": ("action_name",),
}

Problem = tuple[ReasonCode, str, str]


class ConversionPayload(RequestRef, ObservationContext):
    conversion_id: Id
    advertiser_id: Id
    conversion_type: Literal["add_to_cart", "purchase", "custom"]
    action_name: Id | None = None
    order_id: Id | None = None
    revenue: NonNegativeMoney | None = None
    product_id: Id | None = None
    quantity: PositiveInt64 | None = None
    reported_click_id: Id | None = None
    reported_campaign_id: Id | None = None
    reported_ad_id: Id | None = None
    items: list[ConversionItem] = Field(default_factory=list)

    @model_validator(mode="after")
    def _type_specific_rules(self) -> Self:
        required = _REQUIRED_BY_CONVERSION_TYPE[self.conversion_type]
        problems: list[Problem] = [
            (ReasonCode.MISSING_FIELD, name, f"Required for {self.conversion_type} conversions")
            for name in required
            if getattr(self, name) is None
        ]
        if self.items and self.revenue is None and "revenue" not in required:
            problems.append((ReasonCode.MISSING_FIELD, "revenue", "Required when items are present"))
        if self.reported_ad_id is not None and self.reported_campaign_id is None:
            problems.append((ReasonCode.MISSING_FIELD, "reported_campaign_id", "Required when reported_ad_id is present"))
        problems += self._item_problems()
        if problems:
            reject(*problems)
        return self

    def _item_problems(self) -> list[Problem]:
        if not self.items or self.revenue is None:
            return []
        problems: list[Problem] = []
        line_ids = [item.line_item_id for item in self.items]
        if len(set(line_ids)) != len(line_ids):
            problems.append((ReasonCode.INVALID_VALUE, "items", "line_item_id values must be unique"))
        if any(item.revenue.currency != self.revenue.currency for item in self.items):
            problems.append(
                (ReasonCode.INVALID_VALUE, "items", "Item currencies must match the conversion revenue currency")
            )
        elif sum(item.revenue.amount_micros for item in self.items) != self.revenue.amount_micros:
            problems.append((ReasonCode.INVALID_VALUE, "items", "Item revenues must sum exactly to the conversion revenue"))
        return problems


class Envelope(ContractModel):
    event_id: Id
    schema_version: SchemaVersion
    source: Id
    source_event_id: Id
    occurred_at: EventTime
    received_at: UtcTimestamp
    extensions: dict[str, Any] = Field(default_factory=dict)


class ClickEvent(Envelope):
    event_type: Literal["click"]
    payload: ClickPayload


class ImpressionEvent(Envelope):
    event_type: Literal["impression"]
    payload: ImpressionPayload


class ConversionEvent(Envelope):
    event_type: Literal["conversion"]
    payload: ConversionPayload


AnyEvent = ClickEvent | ImpressionEvent | ConversionEvent
EVENT_TYPES = frozenset({"click", "impression", "conversion"})
EVENT_ADAPTER: TypeAdapter[AnyEvent] = TypeAdapter(Annotated[AnyEvent, Field(discriminator="event_type")])
