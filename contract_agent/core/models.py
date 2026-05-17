from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Column:
    name: str
    type: str
    required: bool = False
    description: str = ""
    format: str = ""
    pattern: str = ""
    allowed_values: list[str] = field(default_factory=list)
    min_value: str = ""
    max_value: str = ""

    def normalized_type(self) -> str:
        return normalize_type(self.type)


@dataclass(frozen=True)
class Schema:
    name: str
    columns: list[Column]

    def by_name(self) -> dict[str, Column]:
        return {column.name.lower(): column for column in self.columns}


@dataclass(frozen=True)
class DataContract:
    name: str
    version: str
    owner: str
    columns: list[Column]

    def by_name(self) -> dict[str, Column]:
        return {column.name.lower(): column for column in self.columns}


@dataclass(frozen=True)
class ContractIssue:
    severity: str
    check: str
    column: str
    message: str
    expected: Any = None
    actual: Any = None
    row: int | None = None
    impact: str = ""

    def as_dict(self) -> dict[str, Any]:
        payload = {
            "severity": self.severity,
            "check": self.check,
            "column": self.column,
            "message": self.message,
        }
        if self.expected is not None:
            payload["expected"] = self.expected
        if self.actual is not None:
            payload["actual"] = self.actual
        if self.row is not None:
            payload["row"] = self.row
        if self.impact:
            payload["impact"] = self.impact
        return payload


@dataclass(frozen=True)
class Correction:
    action: str
    target: str
    suggestion: str

    def as_dict(self) -> dict[str, str]:
        return {
            "action": self.action,
            "target": self.target,
            "suggestion": self.suggestion,
        }


@dataclass(frozen=True)
class ContractReport:
    contract: str
    source: str
    status: str
    issues: list[ContractIssue] = field(default_factory=list)
    corrections: list[Correction] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        counts = {
            "FAIL": sum(1 for issue in self.issues if issue.severity == "FAIL"),
            "WARN": sum(1 for issue in self.issues if issue.severity == "WARN"),
            "INFO": sum(1 for issue in self.issues if issue.severity == "INFO"),
        }
        return {
            "contract": self.contract,
            "source": self.source,
            "status": self.status,
            "counts": counts,
            "issues": [issue.as_dict() for issue in self.issues],
            "corrections": [correction.as_dict() for correction in self.corrections],
        }


TYPE_ALIASES = {
    "integer": "int",
    "int32": "int",
    "int64": "long",
    "bigint": "long",
    "string": "string",
    "str": "string",
    "varchar": "string",
    "text": "string",
    "bool": "boolean",
    "boolean": "boolean",
    "double": "double",
    "float64": "double",
    "float": "float",
    "decimal": "decimal",
    "numeric": "decimal",
    "timestamp_ntz": "timestamp",
    "datetime": "timestamp",
    "date": "date",
}


def normalize_type(value: str) -> str:
    raw = str(value or "").strip().lower()
    if "(" in raw:
        base = raw.split("(", 1)[0].strip()
        return TYPE_ALIASES.get(base, base)
    return TYPE_ALIASES.get(raw, raw)
