"""Ingestion validator routing valid canonical events and quarantining failures."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from adstream.adapters.base import AdapterRegistry
from adstream.adapters.ecosystems import create_default_registry
from adstream.domain.exceptions import AdStreamError
from adstream.domain.models import CanonicalAdEvent, QuarantineRecord, SourceSystem
from adstream.ingestion.quarantine import QuarantineSink


@dataclass(frozen=True)
class IngestionResult:
    accepted: list[CanonicalAdEvent]
    quarantined: list[QuarantineRecord]


class IngestionValidator:
    """Validates raw ecosystem payloads and isolates malformed events into QuarantineSink."""

    def __init__(
        self,
        *,
        registry: AdapterRegistry | None = None,
        quarantine: QuarantineSink | None = None,
    ) -> None:
        self.registry = registry or create_default_registry()
        self.quarantine = quarantine or QuarantineSink()

    def validate_one(
        self, source: SourceSystem | str, raw_payload: Any
    ) -> CanonicalAdEvent | QuarantineRecord:
        source_label = source.value if isinstance(source, SourceSystem) else str(source)
        if not isinstance(raw_payload, dict):
            qrec = QuarantineRecord(
                source_system=source_label,
                reason_code="MALFORMED_PAYLOAD_TYPE",
                error_detail=f"Expected dict payload, got {type(raw_payload).__name__}",
                raw_payload=raw_payload,
            )
            self.quarantine.write(qrec)
            return qrec

        try:
            return self.registry.parse(source, raw_payload)
        except AdStreamError as exc:
            qrec = QuarantineRecord(
                source_system=source_label,
                reason_code=exc.error_code,
                error_detail=str(exc),
                raw_payload=raw_payload,
            )
            self.quarantine.write(qrec)
            return qrec

    def validate_stream(
        self, items: Iterable[tuple[SourceSystem | str, Any]]
    ) -> IngestionResult:
        accepted: list[CanonicalAdEvent] = []
        quarantined: list[QuarantineRecord] = []
        for source, raw in items:
            outcome = self.validate_one(source, raw)
            if isinstance(outcome, QuarantineRecord):
                quarantined.append(outcome)
            else:
                accepted.append(outcome)
        return IngestionResult(accepted=accepted, quarantined=quarantined)
