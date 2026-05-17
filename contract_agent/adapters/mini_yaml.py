from __future__ import annotations

from typing import Any


def parse_contract_yaml(text: str) -> dict[str, Any]:
    """Parse the small YAML subset used by starter data contracts.

    Supported shape:
      key: value
      columns:
        - name: id
          type: long
          required: true
    """
    payload: dict[str, Any] = {}
    current_list_name: str | None = None
    current_item: dict[str, Any] | None = None

    for raw_line in text.splitlines():
        line = strip_comment(raw_line).rstrip()
        if not line.strip():
            continue
        stripped = line.strip()
        if stripped.endswith(":") and not stripped.startswith("- "):
            key = stripped[:-1].strip()
            payload[key] = []
            current_list_name = key
            current_item = None
            continue
        if stripped.startswith("- "):
            if current_list_name is None:
                raise ValueError("YAML list item found before a list key")
            current_item = {}
            payload[current_list_name].append(current_item)
            rest = stripped[2:].strip()
            if rest:
                key, value = parse_key_value(rest)
                current_item[key] = parse_scalar(value)
            continue
        key, value = parse_key_value(stripped)
        if current_item is not None and raw_line.startswith((" ", "\t")):
            current_item[key] = parse_scalar(value)
        else:
            payload[key] = parse_scalar(value)
            current_list_name = None
            current_item = None
    return payload


def parse_key_value(line: str) -> tuple[str, str]:
    if ":" not in line:
        raise ValueError(f"Invalid YAML line: {line}")
    key, value = line.split(":", 1)
    return key.strip(), value.strip()


def parse_scalar(value: str) -> Any:
    clean = value.strip().strip('"').strip("'")
    if clean.startswith("[") and clean.endswith("]"):
        raw_items = clean[1:-1].strip()
        if not raw_items:
            return []
        return [item.strip().strip('"').strip("'") for item in raw_items.split(",")]
    lowered = clean.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered in {"null", "none", "~"}:
        return None
    return clean


def strip_comment(line: str) -> str:
    in_single = False
    in_double = False
    for index, char in enumerate(line):
        if char == "'" and not in_double:
            in_single = not in_single
        elif char == '"' and not in_single:
            in_double = not in_double
        elif char == "#" and not in_single and not in_double:
            return line[:index]
    return line
