from __future__ import annotations

from typing import Any

from contract_agent.core.models import Column, DataContract


def contract_from_mapping(payload: dict[str, Any]) -> DataContract:
    columns_payload = payload.get("columns") or []
    if not isinstance(columns_payload, list):
        raise ValueError("contract.columns must be a list")
    return DataContract(
        name=str(payload.get("name") or payload.get("dataset") or "unnamed-contract"),
        version=str(payload.get("version") or "0.1.0"),
        owner=str(payload.get("owner") or "unknown"),
        columns=[column_from_mapping(item) for item in columns_payload if isinstance(item, dict)],
    )


def column_from_mapping(payload: dict[str, Any]) -> Column:
    name = payload.get("name")
    if not name:
        raise ValueError("column.name is required")
    return Column(
        name=str(name),
        type=str(payload.get("type") or "string"),
        required=as_bool(payload.get("required", False)),
        description=str(payload.get("description") or ""),
        format=str(payload.get("format") or ""),
        pattern=str(payload.get("pattern") or ""),
        allowed_values=[str(item) for item in as_list(payload.get("allowed_values") or payload.get("allowedValues"))],
        min_value=as_optional_str(first_present(payload, ("min", "min_value", "minValue"))),
        max_value=as_optional_str(first_present(payload, ("max", "max_value", "maxValue"))),
    )


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "yes", "1", "required"}
    return bool(value)


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def first_present(payload: dict[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        if key in payload:
            return payload[key]
    return None


def as_optional_str(value: Any) -> str:
    if value is None:
        return ""
    return str(value)
