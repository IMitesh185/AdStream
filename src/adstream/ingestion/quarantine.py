"""Durable quarantine sink for invalid, unparseable, or schema-incompatible payloads."""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Iterable

from adstream.domain.models import QuarantineRecord


class QuarantineSink:
    """Collects quarantined payloads in memory and optionally persists them to JSONL."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path
        self._lock = threading.Lock()
        self._records: list[QuarantineRecord] = []
        if self.path is not None:
            self.path.parent.mkdir(parents=True, exist_ok=True)

    def write(self, record: QuarantineRecord) -> None:
        line = record.model_dump_json()
        with self._lock:
            self._records.append(record)
            if self.path is not None:
                with self.path.open("a", encoding="utf-8") as fh:
                    fh.write(line + "\n")

    def write_batch(self, records: Iterable[QuarantineRecord]) -> int:
        batch = list(records)
        if not batch:
            return 0
        lines = [rec.model_dump_json() for rec in batch]
        with self._lock:
            self._records.extend(batch)
            if self.path is not None:
                with self.path.open("a", encoding="utf-8") as fh:
                    fh.write("\n".join(lines) + "\n")
        return len(batch)

    @property
    def records(self) -> list[QuarantineRecord]:
        with self._lock:
            return list(self._records)

    def count(self) -> int:
        with self._lock:
            return len(self._records)

    def summary_by_reason(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        with self._lock:
            for rec in self._records:
                counts[rec.reason_code] = counts.get(rec.reason_code, 0) + 1
        return counts

    def read_persisted(self) -> list[dict[str, object]]:
        if self.path is None or not self.path.exists():
            return []
        with self.path.open("r", encoding="utf-8") as fh:
            return [json.loads(line) for line in fh if line.strip()]
