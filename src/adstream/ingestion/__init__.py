"""Ingestion boundary: payload validation and durable JSONL quarantine."""

from adstream.ingestion.quarantine import QuarantineSink
from adstream.ingestion.validator import IngestionResult, IngestionValidator

__all__ = [
    "IngestionResult",
    "IngestionValidator",
    "QuarantineSink",
]
