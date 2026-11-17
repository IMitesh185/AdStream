"""Adapter protocol, registry, and canonical event dispatcher."""

from __future__ import annotations

from typing import Any, Protocol, Type

from pydantic import ValidationError

from adstream.domain.exceptions import InvalidEventError, SchemaCompatibilityError
from adstream.domain.models import (
    AdRequestEvent,
    AuctionOutcomeEvent,
    BaseAdEvent,
    BidEvent,
    BillingAdjustmentEvent,
    BudgetEvent,
    CanonicalAdEvent,
    ClickEvent,
    ConversionEvent,
    EventType,
    ImpressionEvent,
    InvalidTrafficEvent,
    SourceSystem,
    VideoInteractionEvent,
)

SUPPORTED_SCHEMA_VERSIONS: frozenset[int] = frozenset({1, 2})

_EVENT_MODEL_BY_TYPE: dict[EventType, Type[BaseAdEvent]] = {
    EventType.AD_REQUEST: AdRequestEvent,
    EventType.BID: BidEvent,
    EventType.AUCTION_OUTCOME: AuctionOutcomeEvent,
    EventType.IMPRESSION: ImpressionEvent,
    EventType.CLICK: ClickEvent,
    EventType.VIDEO_INTERACTION: VideoInteractionEvent,
    EventType.CONVERSION: ConversionEvent,
    EventType.INVALID_TRAFFIC: InvalidTrafficEvent,
    EventType.BUDGET: BudgetEvent,
    EventType.BILLING_ADJUSTMENT: BillingAdjustmentEvent,
}


class SourceAdapter(Protocol):
    """Protocol implemented by every ecosystem-specific source adapter."""

    source_system: SourceSystem

    def to_canonical(self, raw: dict[str, Any]) -> CanonicalAdEvent:
        """Transform a raw source payload into a validated canonical AdStream event."""
        ...


def build_canonical_event(
    payload: dict[str, Any],
    *,
    raw_payload: dict[str, Any],
    supported_versions: frozenset[int] = SUPPORTED_SCHEMA_VERSIONS,
) -> CanonicalAdEvent:
    """Validate schema version and dispatch to the exact event-family contract."""
    if not isinstance(payload, dict):
        raise InvalidEventError("Normalized payload must be a JSON object")

    schema_version = payload.get("schema_version", 1)
    if isinstance(schema_version, bool) or not isinstance(schema_version, int):
        raise InvalidEventError(f"Invalid schema_version type: {type(schema_version).__name__}")
    if schema_version not in supported_versions:
        raise SchemaCompatibilityError(
            f"Unsupported schema_version={schema_version}; supported={sorted(supported_versions)}"
        )

    raw_type = payload.get("event_type")
    try:
        event_type = EventType(raw_type)
    except ValueError as exc:
        raise InvalidEventError(f"Unknown event_type={raw_type!r}") from exc

    model_cls = _EVENT_MODEL_BY_TYPE[event_type]
    merged = {**payload, "raw_payload": raw_payload}
    try:
        return model_cls.model_validate(merged)  # type: ignore[return-value]
    except ValidationError as exc:
        raise InvalidEventError(f"Contract validation failed: {exc}") from exc


class AdapterRegistry:
    """Routes incoming raw payloads to the registered ecosystem adapter."""

    def __init__(self) -> None:
        self._adapters: dict[SourceSystem, SourceAdapter] = {}

    def register(self, adapter: SourceAdapter) -> None:
        self._adapters[adapter.source_system] = adapter

    def parse(self, source: SourceSystem | str, raw: dict[str, Any]) -> CanonicalAdEvent:
        try:
            source_enum = source if isinstance(source, SourceSystem) else SourceSystem(source)
        except ValueError as exc:
            raise InvalidEventError(f"Unsupported source_system={source!r}") from exc

        adapter = self._adapters.get(source_enum)
        if adapter is None:
            raise InvalidEventError(f"No adapter registered for source_system={source_enum.value}")
        return adapter.to_canonical(raw)
