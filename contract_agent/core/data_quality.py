from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from contract_agent.core.agent import status_for
from contract_agent.core.models import Column, ContractIssue, ContractReport, Correction, DataContract


@dataclass
class DataQualityAgent:
    max_issues_per_check: int = 20

    def evaluate_rows(
        self,
        rows: list[dict[str, str]],
        contract: DataContract,
        source_name: str,
    ) -> ContractReport:
        issues: list[ContractIssue] = []
        corrections: list[Correction] = []
        correction_keys: set[tuple[str, str]] = set()

        indexed_rows = [
            (row_index, {name.lower(): value for name, value in row.items()})
            for row_index, row in enumerate(rows, start=2)
        ]
        for column in contract.columns:
            empty_rows: list[int] = []
            for row_index, row_by_name in indexed_rows:
                if len(issues) >= self.max_issues_per_check:
                    break
                if column.name.lower() not in row_by_name:
                    continue
                value = row_by_name[column.name.lower()]
                if column.required and is_blank(value):
                    empty_rows.append(row_index)
                    continue
                issue = validate_value(column, value, row_index, check_required=False)
                if issue is None:
                    continue
                issues.append(issue)
                add_correction(corrections, correction_keys, correction_for_issue(issue, column))
            if empty_rows and len(issues) < self.max_issues_per_check:
                issue = required_values_issue(column, empty_rows)
                issues.append(issue)
                add_correction(corrections, correction_keys, correction_for_issue(issue, column))

        if len(issues) >= self.max_issues_per_check:
            issues.append(
                ContractIssue(
                    severity="WARN",
                    check="quality.issue_limit",
                    column="*",
                    message="Data quality validation stopped after reaching the issue sample limit.",
                    expected=f"at most {self.max_issues_per_check} sampled issues",
                    actual=f"{len(issues)} sampled issues",
                    impact="There may be more invalid rows than the report sample shows.",
                )
            )

        return ContractReport(
            contract=contract.name,
            source=source_name,
            status=status_for(issues),
            issues=issues,
            corrections=corrections,
        )


def validate_value(column: Column, raw_value: Any, row_index: int, check_required: bool = True) -> ContractIssue | None:
    value = "" if raw_value is None else str(raw_value).strip()
    if check_required and column.required and value == "":
        return ContractIssue(
            severity="FAIL",
            check="value.required",
            column=column.name,
            message="Required value is empty.",
            expected="non-empty value",
            actual="empty",
            row=row_index,
            impact="Mandatory fields with null-like values can break joins, primary keys, and downstream metrics.",
        )
    if value == "":
        return None

    if column.allowed_values and value not in column.allowed_values:
        return ContractIssue(
            severity="FAIL",
            check="value.allowed",
            column=column.name,
            message="Value is outside the allowed domain.",
            expected=column.allowed_values,
            actual=redact_value(value),
            row=row_index,
            impact="Unexpected domain values can corrupt aggregations, filters, and business rules.",
        )

    if column.pattern and re.fullmatch(column.pattern, value) is None:
        return ContractIssue(
            severity="FAIL",
            check="value.pattern",
            column=column.name,
            message="Value does not match the expected pattern.",
            expected=column.pattern,
            actual=redact_value(value),
            row=row_index,
            impact="Consumers may reject the value or produce incorrect joins and dimensions.",
        )

    if column.format and column.normalized_type() in {"date", "timestamp"}:
        if not matches_format(value, column.format):
            return ContractIssue(
                severity="FAIL",
                check="value.format",
                column=column.name,
                message="Date or timestamp value does not match the contract format.",
                expected=column.format,
                actual=redact_value(value),
                row=row_index,
                impact="Date parsing can fail or silently swap day and month depending on the runtime locale.",
            )
        return None

    if not matches_type(value, column.normalized_type()):
        return ContractIssue(
            severity="FAIL",
            check="value.type",
            column=column.name,
            message="Value cannot be parsed as the expected contract type.",
            expected=column.type,
            actual=redact_value(value),
            row=row_index,
            impact="Spark, warehouses, or Iceberg writers may fail during casting or write invalid data.",
        )
    numeric_issue = validate_numeric_bounds(column, value, row_index)
    if numeric_issue is not None:
        return numeric_issue
    return None


def required_values_issue(column: Column, rows: list[int]) -> ContractIssue:
    count = len(rows)
    return ContractIssue(
        severity="FAIL",
        check="value.required",
        column=column.name,
        message=f"{count} required values are empty.",
        expected="non-empty value",
        actual=f"{count} empty values",
        row=rows[0],
        impact="Mandatory fields with null-like values can break joins, primary keys, and downstream metrics.",
    )


def matches_type(value: str, normalized_type: str) -> bool:
    if normalized_type == "string":
        return True
    if normalized_type in {"int", "long"}:
        return can_parse_int(value)
    if normalized_type in {"float", "double"}:
        return can_parse_float(value)
    if normalized_type == "decimal":
        return can_parse_decimal(value)
    if normalized_type == "boolean":
        return value.lower() in {"true", "false", "1", "0", "yes", "no"}
    if normalized_type == "date":
        return can_parse_iso_date(value)
    if normalized_type == "timestamp":
        return can_parse_iso_timestamp(value)
    return True


def validate_numeric_bounds(column: Column, value: str, row_index: int) -> ContractIssue | None:
    if column.normalized_type() not in {"int", "long", "float", "double", "decimal"}:
        return None
    numeric = parse_decimal(value)
    if numeric is None:
        return None
    if column.min_value:
        minimum = parse_decimal(column.min_value)
        if minimum is not None and numeric < minimum:
            return ContractIssue(
                severity="FAIL",
                check="value.min",
                column=column.name,
                message="Numeric value is lower than the contract minimum.",
                expected=f">= {column.min_value}",
                actual=redact_value(value),
                row=row_index,
                impact="Negative or too-small values can corrupt financial metrics and downstream controls.",
            )
    if column.max_value:
        maximum = parse_decimal(column.max_value)
        if maximum is not None and numeric > maximum:
            return ContractIssue(
                severity="FAIL",
                check="value.max",
                column=column.name,
                message="Numeric value is higher than the contract maximum.",
                expected=f"<= {column.max_value}",
                actual=redact_value(value),
                row=row_index,
                impact="Out-of-range values can corrupt metrics, anomaly detection, and business rules.",
            )
    return None


def matches_format(value: str, expected_format: str) -> bool:
    try:
        datetime.strptime(value, expected_format)
        return True
    except ValueError:
        return False


def can_parse_int(value: str) -> bool:
    try:
        int(value)
        return True
    except ValueError:
        return False


def can_parse_float(value: str) -> bool:
    try:
        float(value)
        return True
    except ValueError:
        return False


def can_parse_decimal(value: str) -> bool:
    return parse_decimal(value) is not None


def parse_decimal(value: str) -> Decimal | None:
    try:
        return Decimal(value)
    except InvalidOperation:
        return None


def can_parse_iso_date(value: str) -> bool:
    try:
        date.fromisoformat(value)
        return True
    except ValueError:
        return False


def can_parse_iso_timestamp(value: str) -> bool:
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
        return True
    except ValueError:
        return False


def correction_for_issue(issue: ContractIssue, column: Column) -> Correction:
    if issue.check == "value.required":
        return Correction(
            action="FILL_REQUIRED_VALUE",
            target=column.name,
            suggestion=f"Reject or quarantine rows where `{column.name}` is empty, or populate it before delivery.",
        )
    if issue.check == "value.format":
        return Correction(
            action="NORMALIZE_DATE_FORMAT",
            target=column.name,
            suggestion=f"Normalize `{column.name}` to `{column.format}` before the append or update the contract intentionally.",
        )
    if issue.check == "value.allowed":
        return Correction(
            action="MAP_ALLOWED_VALUE",
            target=column.name,
            suggestion=f"Map `{column.name}` to one of the accepted contract values: {', '.join(column.allowed_values)}.",
        )
    if issue.check == "value.pattern":
        return Correction(
            action="FIX_VALUE_PATTERN",
            target=column.name,
            suggestion=f"Clean `{column.name}` so it matches the contract pattern `{column.pattern}`.",
        )
    if issue.check == "value.min":
        return Correction(
            action="ENFORCE_MIN_VALUE",
            target=column.name,
            suggestion=f"Reject rows where `{column.name}` is lower than `{column.min_value}` or fix the producer rule.",
        )
    if issue.check == "value.max":
        return Correction(
            action="ENFORCE_MAX_VALUE",
            target=column.name,
            suggestion=f"Reject rows where `{column.name}` is higher than `{column.max_value}` or fix the producer rule.",
        )
    return Correction(
        action="CAST_OR_CLEAN_VALUE",
        target=column.name,
        suggestion=f"Cast or clean `{column.name}` so every value can be parsed as `{column.type}`.",
    )


def merge_reports(schema_report: ContractReport, quality_report: ContractReport | None) -> ContractReport:
    if quality_report is None:
        return schema_report
    issues = [*schema_report.issues, *quality_report.issues]
    corrections = dedupe_corrections([*schema_report.corrections, *quality_report.corrections])
    return ContractReport(
        contract=schema_report.contract,
        source=schema_report.source,
        status=status_for(issues),
        issues=issues,
        corrections=corrections,
    )


def dedupe_corrections(corrections: list[Correction]) -> list[Correction]:
    seen: set[tuple[str, str]] = set()
    result: list[Correction] = []
    for correction in corrections:
        key = (correction.action, correction.target)
        if key not in seen:
            seen.add(key)
            result.append(correction)
    return result


def redact_value(value: str) -> str:
    if "@" in value:
        name, _, domain = value.partition("@")
        return f"{name[:1]}***@{domain}"
    if len(value) > 80:
        return f"{value[:77]}..."
    return value


def is_blank(value: Any) -> bool:
    return value is None or str(value).strip() == ""


def add_correction(
    corrections: list[Correction],
    correction_keys: set[tuple[str, str]],
    correction: Correction,
) -> None:
    key = (correction.action, correction.target)
    if key in correction_keys:
        return
    correction_keys.add(key)
    corrections.append(correction)
