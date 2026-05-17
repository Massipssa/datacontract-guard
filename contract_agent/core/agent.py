from __future__ import annotations

from dataclasses import dataclass

from contract_agent.core.models import Column, ContractIssue, ContractReport, Correction, DataContract, Schema


SAFE_PROMOTIONS = {
    ("int", "long"),
    ("float", "double"),
}


@dataclass
class DataContractAgent:
    allow_safe_promotion: bool = True
    warn_extra_columns: bool = True

    def evaluate(self, source_schema: Schema, contract: DataContract) -> ContractReport:
        issues: list[ContractIssue] = []
        corrections: list[Correction] = []
        source_by_name = source_schema.by_name()
        contract_names = set(contract.by_name())
        extra_columns = [
            source_column
            for source_column in source_schema.columns
            if source_column.name.lower() not in contract_names
        ]
        renamed_source_names: set[str] = set()

        for expected in contract.columns:
            source_column = source_by_name.get(expected.name.lower())
            if source_column is None:
                renamed_from = find_rename_candidate(expected, extra_columns)
                if renamed_from is not None:
                    renamed_source_names.add(renamed_from.name.lower())
                    issues.append(
                        ContractIssue(
                            severity="FAIL",
                            check="column.renamed",
                            column=expected.name,
                            message="A required contract column appears to have been renamed in the source file.",
                            expected=expected.name,
                            actual=renamed_from.name,
                            impact="Downstream jobs may read nulls or fail because the expected field name is no longer present.",
                        )
                    )
                    corrections.append(rename_source_column_correction(expected, renamed_from))
                    continue
                severity = "FAIL" if expected.required else "WARN"
                issues.append(
                    ContractIssue(
                        severity=severity,
                        check="column.missing",
                        column=expected.name,
                        message="Column declared in the contract is missing from the source schema.",
                        expected=expected.type,
                        actual=None,
                        impact="Pipelines, Iceberg appends, and dashboards that depend on this column can fail or become incomplete.",
                    )
                )
                corrections.append(add_column_correction(expected))
                continue

            if expected.normalized_type() != source_column.normalized_type():
                if self.allow_safe_promotion and is_safe_promotion(expected, source_column):
                    issues.append(
                        ContractIssue(
                            severity="WARN",
                            check="type.promotion",
                            column=expected.name,
                            message="Source type differs but is a safe promotion.",
                            expected=expected.type,
                            actual=source_column.type,
                            impact="The pipeline can usually continue, but the contract should be updated intentionally.",
                        )
                    )
                    corrections.append(update_contract_type_correction(expected, source_column))
                else:
                    issues.append(
                        ContractIssue(
                            severity="FAIL",
                            check="type.change",
                            column=expected.name,
                            message="Source type is incompatible with the contract.",
                            expected=expected.type,
                            actual=source_column.type,
                            impact="Spark, Iceberg writes, or BI models may fail or silently coerce values incorrectly.",
                        )
                    )
                    corrections.append(cast_source_column_correction(expected, source_column))

        if self.warn_extra_columns:
            for source_column in extra_columns:
                if source_column.name.lower() not in renamed_source_names:
                    issues.append(
                        ContractIssue(
                            severity="WARN",
                            check="column.extra",
                            column=source_column.name,
                            message="Source column is not declared in the contract.",
                            expected=None,
                            actual=source_column.type,
                            impact="Unexpected fields can create schema drift and should be accepted explicitly before publication.",
                        )
                    )
                    corrections.append(add_to_contract_correction(source_column))

        return ContractReport(
            contract=contract.name,
            source=source_schema.name,
            status=status_for(issues),
            issues=issues,
            corrections=corrections,
        )


def is_safe_promotion(expected: Column, actual: Column) -> bool:
    return (expected.normalized_type(), actual.normalized_type()) in SAFE_PROMOTIONS


def status_for(issues: list[ContractIssue]) -> str:
    if any(issue.severity == "FAIL" for issue in issues):
        return "FAIL"
    if any(issue.severity == "WARN" for issue in issues):
        return "WARN"
    return "PASS"


def add_column_correction(column: Column) -> Correction:
    return Correction(
        action="ADD_SOURCE_COLUMN",
        target=column.name,
        suggestion=f"Add `{column.name}` as `{column.type}` in the source pipeline or mark it optional in the contract.",
    )


def rename_source_column_correction(expected: Column, actual: Column) -> Correction:
    return Correction(
        action="RENAME_SOURCE_COLUMN",
        target=actual.name,
        suggestion=f"Rename source column `{actual.name}` back to `{expected.name}` or update the contract if the rename is intentional.",
    )


def update_contract_type_correction(expected: Column, actual: Column) -> Correction:
    return Correction(
        action="UPDATE_CONTRACT_TYPE",
        target=expected.name,
        suggestion=f"Update contract column `{expected.name}` from `{expected.type}` to `{actual.type}` if the promotion is accepted.",
    )


def cast_source_column_correction(expected: Column, actual: Column) -> Correction:
    return Correction(
        action="CAST_SOURCE_COLUMN",
        target=expected.name,
        suggestion=f"Cast source column `{actual.name}` from `{actual.type}` to `{expected.type}` before publishing.",
    )


def add_to_contract_correction(column: Column) -> Correction:
    return Correction(
        action="ADD_CONTRACT_COLUMN",
        target=column.name,
        suggestion=f"Add `{column.name}` as `{column.type}` to the contract if this new field is intentional.",
    )


def find_rename_candidate(expected: Column, candidates: list[Column]) -> Column | None:
    for candidate in candidates:
        if looks_like_rename(expected.name, candidate.name):
            return candidate
    return None


def looks_like_rename(expected: str, actual: str) -> bool:
    left = normalize_name(expected)
    right = normalize_name(actual)
    if not left or not right:
        return False
    if left in right or right in left:
        return True
    distance = levenshtein_distance(left, right)
    return distance <= 2 and min(len(left), len(right)) >= 4


def normalize_name(value: str) -> str:
    return "".join(char for char in value.lower() if char.isalnum())


def levenshtein_distance(left: str, right: str) -> int:
    previous = list(range(len(right) + 1))
    for left_index, left_char in enumerate(left, start=1):
        current = [left_index]
        for right_index, right_char in enumerate(right, start=1):
            cost = 0 if left_char == right_char else 1
            current.append(
                min(
                    current[right_index - 1] + 1,
                    previous[right_index] + 1,
                    previous[right_index - 1] + cost,
                )
            )
        previous = current
    return previous[-1]
