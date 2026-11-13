import hashlib
import json
from dataclasses import dataclass
from typing import Any, NoReturn

from pydantic import ValidationError
from pydantic_core import ErrorDetails

from .context import ValidationContext
from .errors import ReasonCode, ValidationIssue
from .events import EVENT_ADAPTER, EVENT_TYPES, AnyEvent
from .quarantine import QuarantineRecord

_MAX_TEXT = 200

_CODE_BY_PYDANTIC_TYPE = {
    "missing": ReasonCode.MISSING_FIELD,
    "extra_forbidden": ReasonCode.UNDECLARED_FIELD,
    "union_tag_invalid": ReasonCode.UNKNOWN_EVENT_TYPE,
    "union_tag_not_found": ReasonCode.MISSING_FIELD,
    "literal_error": ReasonCode.INVALID_VALUE,
    "string_pattern_mismatch": ReasonCode.INVALID_VALUE,
    "greater_than": ReasonCode.OUT_OF_RANGE,
    "greater_than_equal": ReasonCode.OUT_OF_RANGE,
    "less_than": ReasonCode.OUT_OF_RANGE,
    "less_than_equal": ReasonCode.OUT_OF_RANGE,
}


@dataclass(frozen=True)
class Accepted:
    event: AnyEvent
    raw_payload_sha256: str


@dataclass(frozen=True)
class Quarantined:
    record: QuarantineRecord


Outcome = Accepted | Quarantined


def validate_event(raw: bytes, *, receipt_id: str, context: ValidationContext) -> Outcome:
    """Check one incoming event against its contract. Bad input is quarantined, never raised."""
    digest = hashlib.sha256(raw).hexdigest()
    try:
        data = json.loads(raw, object_pairs_hook=_reject_duplicate_keys, parse_constant=_reject_constant)
    except (ValueError, RecursionError) as exc:
        issue = ValidationIssue(code=ReasonCode.MALFORMED_JSON, field_path="", message=str(exc)[:_MAX_TEXT])
        return _quarantine(digest, receipt_id, context, None, [issue])

    if isinstance(data, dict):
        # Ingestion assigns the receipt time; a value sent by the producer is never trusted.
        data["received_at"] = context.now.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    try:
        event = EVENT_ADAPTER.validate_python(data, context=context)
    except ValidationError as exc:
        return _quarantine(digest, receipt_id, context, data, _issues_from(exc))
    return Accepted(event=event, raw_payload_sha256=digest)


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    keys = [key for key, _ in pairs]
    if len(keys) != len(set(keys)):
        raise ValueError("A JSON object repeats a key")
    return dict(pairs)


def _reject_constant(name: str) -> NoReturn:
    raise ValueError(f"{name} is not valid JSON")


def _issues_from(exc: ValidationError) -> list[ValidationIssue]:
    errors = exc.errors(include_url=False, include_context=False, include_input=True)
    return [_issue_from(error) for error in errors]


def _issue_from(error: ErrorDetails) -> ValidationIssue:
    kind = error["type"]
    location = tuple(error["loc"])
    if location and location[0] in EVENT_TYPES:
        # Errors inside a union branch start with the branch tag (the event_type value).
        location = location[1:]
    if kind in ("union_tag_invalid", "union_tag_not_found"):
        location = ("event_type",)
    code = _code_for(kind)
    if code is ReasonCode.INVALID_TYPE and error["input"] is None and location:
        code = ReasonCode.MISSING_FIELD
    path = "".join("/" + str(part).replace("~", "~0").replace("/", "~1") for part in location)
    return ValidationIssue(code=code, field_path=path, message=error["msg"][:_MAX_TEXT])


def _code_for(kind: str) -> ReasonCode:
    try:
        return ReasonCode(kind)
    except ValueError:
        pass
    if kind in _CODE_BY_PYDANTIC_TYPE:
        return _CODE_BY_PYDANTIC_TYPE[kind]
    if kind.endswith("_type"):
        return ReasonCode.INVALID_TYPE
    return ReasonCode.INVALID_VALUE


def _quarantine(
    digest: str,
    receipt_id: str,
    context: ValidationContext,
    data: Any,
    issues: list[ValidationIssue],
) -> Quarantined:
    seen = data if isinstance(data, dict) else {}
    record = QuarantineRecord(
        quarantine_id=f"q-{receipt_id}",
        receipt_id=receipt_id,
        event_id=_short_text(seen.get("event_id")),
        event_type=_short_text(seen.get("event_type")),
        observed_schema_version=_short_text(seen.get("schema_version")),
        stage="schema",
        errors=issues,
        # Placeholder reference: ingestion will store the bytes and supply the real one.
        raw_payload_ref=f"sha256:{digest}",
        raw_payload_sha256=digest,
        received_at=context.now,
        quarantined_at=context.now,
    )
    return Quarantined(record)


def _short_text(value: object) -> str | None:
    if isinstance(value, (str, int)) and not isinstance(value, bool):
        text = str(value)
        if text.strip() and len(text) <= _MAX_TEXT:
            return text
    return None
