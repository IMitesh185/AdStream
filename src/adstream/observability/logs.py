"""Structured JSON application logger with file persistence and live UI tailing."""

from __future__ import annotations

import json
import logging
import threading
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class StructuredLogStore:
    """Thread-safe structured application log sink backed by disk JSONL + ring buffer."""

    def __init__(self, log_path: Path = Path("data/workbench/logs/adstream.log"), max_entries: int = 500) -> None:
        self.log_path = log_path
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._buffer: deque[dict[str, Any]] = deque(maxlen=max_entries)

    def emit(
        self,
        level: str,
        component: str,
        message: str,
        *,
        run_id: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level.upper(),
            "component": component,
            "run_id": run_id,
            "message": message,
            "extra": extra or {},
        }
        line = json.dumps(entry, default=str)
        with self._lock:
            self._buffer.appendleft(entry)
            with self.log_path.open("a", encoding="utf-8") as fh:
                fh.write(line + "\n")
        return entry

    def clear(self) -> None:
        with self._lock:
            self._buffer.clear()
            if self.log_path.exists():
                self.log_path.unlink()

    def tail(self, *, level: str | None = None, run_id: str | None = None, limit: int = 120) -> list[dict[str, Any]]:
        with self._lock:
            items = list(self._buffer)
        if level and level.upper() != "ALL":
            lvl = level.upper()
            items = [i for i in items if i["level"] == lvl]
        if run_id:
            items = [i for i in items if i["run_id"] == run_id]
        return items[:limit]


def configure_python_logger(store: StructuredLogStore) -> logging.Logger:
    """Attach a Python stdlib logging handler forwarding records into StructuredLogStore."""

    class _StoreHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            store.emit(
                record.levelname,
                record.name,
                record.getMessage(),
                run_id=getattr(record, "run_id", None),
            )

    logger = logging.getLogger("adstream")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    logger.addHandler(_StoreHandler())
    logger.propagate = False
    return logger
