from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from contract_agent.core.contract import column_from_mapping, contract_from_mapping
from contract_agent.core.models import Column, DataContract, Schema
from contract_agent.adapters.mini_yaml import parse_contract_yaml


def read_contract(path: Path) -> DataContract:
    suffix = path.suffix.lower()
    text = path.read_text(encoding="utf-8")
    if suffix in {".yaml", ".yml"}:
        return contract_from_mapping(parse_contract_yaml(text))
    if suffix == ".json":
        return contract_from_mapping(json.loads(text))
    raise ValueError("Contract must be YAML or JSON")


def read_source_schema(path: Path, name: str | None = None) -> Schema:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return infer_csv_schema(path, name or path.stem)
    if suffix == ".parquet":
        return infer_parquet_schema(path, name or path.stem)
    if suffix == ".json":
        return read_json_schema(path, name or path.stem)
    raise ValueError("Source schema must be JSON, CSV, or Parquet")


def read_json_schema(path: Path, name: str) -> Schema:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict) and "columns" in payload:
        columns = [column_from_mapping(item) for item in payload["columns"] if isinstance(item, dict)]
        return Schema(name=str(payload.get("name") or name), columns=columns)
    if isinstance(payload, list):
        return Schema(name=name, columns=[column_from_mapping(item) for item in payload if isinstance(item, dict)])
    raise ValueError("JSON source schema must be {columns:[...]} or a list of columns")


def infer_csv_schema(path: Path, name: str) -> Schema:
    rows = read_csv_rows(path, limit=100)
    if not rows:
        raise ValueError("CSV source must contain at least one data row")
    columns = []
    for column_name in rows[0].keys():
        values = [row.get(column_name) for row in rows]
        columns.append(Column(name=column_name, type=infer_type(values)))
    return Schema(name=name, columns=columns)


def read_csv_rows(path: Path, limit: int | None = None) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if limit is None:
            return [row for row in reader]
        return [row for _, row in zip(range(limit), reader)]


def read_data_rows(path: Path, limit: int | None = None) -> list[dict[str, Any]]:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return read_csv_rows(path, limit=limit)
    if suffix == ".parquet":
        return read_parquet_rows(path, limit=limit)
    raise ValueError("Data quality validation currently supports CSV and Parquet files")


def infer_parquet_schema(path: Path, name: str) -> Schema:
    pyarrow, parquet = import_pyarrow()
    arrow_schema = parquet.read_schema(path)
    columns = [
        Column(name=field.name, type=arrow_type_to_contract_type(field.type, pyarrow), required=not field.nullable)
        for field in arrow_schema
    ]
    return Schema(name=name, columns=columns)


def read_parquet_rows(path: Path, limit: int | None = None) -> list[dict[str, Any]]:
    _, parquet = import_pyarrow()
    table = parquet.read_table(path)
    rows = table.to_pylist()
    if limit is None:
        return rows
    return rows[:limit]


def import_pyarrow():
    try:
        import pyarrow as pyarrow  # type: ignore
        import pyarrow.parquet as parquet  # type: ignore
    except ImportError as exc:
        raise ValueError("Parquet support requires the optional dependency `pyarrow`") from exc
    return pyarrow, parquet


def arrow_type_to_contract_type(arrow_type: Any, pyarrow: Any) -> str:
    if pyarrow.types.is_boolean(arrow_type):
        return "boolean"
    if pyarrow.types.is_integer(arrow_type):
        return "long"
    if pyarrow.types.is_floating(arrow_type):
        return "double"
    if pyarrow.types.is_decimal(arrow_type):
        return "decimal"
    if pyarrow.types.is_date(arrow_type):
        return "date"
    if pyarrow.types.is_timestamp(arrow_type):
        return "timestamp"
    if pyarrow.types.is_string(arrow_type) or pyarrow.types.is_large_string(arrow_type):
        return "string"
    return "string"


def infer_type(values: list[Any]) -> str:
    clean = [str(value).strip() for value in values if value not in (None, "")]
    if not clean:
        return "string"
    if all(is_int(value) for value in clean):
        return "long"
    if all(is_float(value) for value in clean):
        return "double"
    if all(value.lower() in {"true", "false"} for value in clean):
        return "boolean"
    return "string"


def is_int(value: str) -> bool:
    try:
        int(value)
        return True
    except ValueError:
        return False


def is_float(value: str) -> bool:
    try:
        float(value)
        return True
    except ValueError:
        return False
