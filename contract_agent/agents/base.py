from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class AgentStep:
    name: str
    status: str
    summary: str
    details: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status,
            "summary": self.summary,
            "details": self.details,
        }


def ok_step(name: str, summary: str, **details: Any) -> AgentStep:
    return AgentStep(name=name, status="OK", summary=summary, details=details)
