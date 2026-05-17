from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Trace:
    trace_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    started_at: float = field(default_factory=time.perf_counter)
    spans: list[dict[str, Any]] = field(default_factory=list)

    def span(self, name: str, **fields: Any) -> None:
        self.spans.append({"name": name, "elapsedMs": self.elapsed_ms(), **fields})

    def elapsed_ms(self) -> int:
        return int((time.perf_counter() - self.started_at) * 1000)

    def as_dict(self) -> dict[str, Any]:
        return {
            "traceId": self.trace_id,
            "elapsedMs": self.elapsed_ms(),
            "spans": self.spans,
        }
