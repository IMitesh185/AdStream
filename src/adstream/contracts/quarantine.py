from typing import Annotated, Literal

from pydantic import Field, StringConstraints

from .errors import ValidationIssue
from .primitives import ContractModel, Id, UtcTimestamp

Stage = Literal["adaptation", "schema", "identity", "reference", "financial"]
Sha256 = Annotated[str, StringConstraints(strict=True, pattern=r"^[0-9a-f]{64}$")]


class QuarantineRecord(ContractModel):
    quarantine_id: Id
    receipt_id: Id
    source: Id | None = None
    event_id: Id | None = None
    event_type: str | None = None
    observed_schema_version: str | None = None
    stage: Stage
    errors: list[ValidationIssue] = Field(min_length=1)
    raw_payload_ref: Id
    raw_payload_sha256: Sha256
    received_at: UtcTimestamp
    quarantined_at: UtcTimestamp
    adapter_version: Id | None = None
