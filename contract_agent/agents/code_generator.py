from __future__ import annotations

from dataclasses import dataclass

from contract_agent.core.models import ContractIssue, ContractReport


@dataclass(frozen=True)
class GeneratedCode:
    title: str
    language: str
    code: str
    related_checks: list[str]

    def as_dict(self) -> dict[str, object]:
        return {
            "title": self.title,
            "language": self.language,
            "code": self.code,
            "relatedChecks": self.related_checks,
        }


class CodeGeneratorAgent:
    name = "Code Generator Agent"

    def generate(self, report: ContractReport) -> list[GeneratedCode]:
        snippets = [
            snippet
            for issue in report.issues
            for snippet in [snippet_for_issue(issue)]
            if snippet is not None
        ]
        return dedupe_snippets(snippets)


def snippet_for_issue(issue: ContractIssue) -> GeneratedCode | None:
    if issue.check == "column.renamed" and issue.actual:
        return GeneratedCode(
            title=f"Rename {issue.actual} to {issue.expected}",
            language="pyspark",
            code=(
                "from pyspark.sql.functions import col\n\n"
                f'df = df.withColumnRenamed("{issue.actual}", "{issue.expected}")'
            ),
            related_checks=[issue.check],
        )
    if issue.check == "type.change":
        return GeneratedCode(
            title=f"Cast {issue.column} to {issue.expected}",
            language="pyspark",
            code=(
                "from pyspark.sql.functions import col\n\n"
                f'df = df.withColumn("{issue.column}", col("{issue.column}").cast("{issue.expected}"))'
            ),
            related_checks=[issue.check],
        )
    if issue.check == "value.required":
        return GeneratedCode(
            title=f"Quarantine rows with empty {issue.column}",
            language="pyspark",
            code=(
                "from pyspark.sql.functions import col, trim\n\n"
                f'invalid_rows = df.filter(col("{issue.column}").isNull() | (trim(col("{issue.column}")) == ""))\n'
                f'valid_rows = df.filter(col("{issue.column}").isNotNull() & (trim(col("{issue.column}")) != ""))'
            ),
            related_checks=[issue.check],
        )
    if issue.check == "value.format":
        return GeneratedCode(
            title=f"Normalize {issue.column} format",
            language="pyspark",
            code=(
                "from pyspark.sql.functions import col, to_date\n\n"
                f'df = df.withColumn("{issue.column}", to_date(col("{issue.column}"), "{spark_date_format(str(issue.expected))}"))'
            ),
            related_checks=[issue.check],
        )
    if issue.check == "value.type":
        return GeneratedCode(
            title=f"Clean or cast {issue.column}",
            language="pyspark",
            code=(
                "from pyspark.sql.functions import col\n\n"
                f'df = df.withColumn("{issue.column}", col("{issue.column}").cast("{issue.expected}"))'
            ),
            related_checks=[issue.check],
        )
    if issue.check == "value.min":
        return GeneratedCode(
            title=f"Reject {issue.column} below minimum",
            language="pyspark",
            code=(
                "from pyspark.sql.functions import col\n\n"
                f'valid_rows = df.filter(col("{issue.column}") >= {bound_value(str(issue.expected))})\n'
                f'invalid_rows = df.filter(col("{issue.column}") < {bound_value(str(issue.expected))})'
            ),
            related_checks=[issue.check],
        )
    if issue.check == "column.extra":
        return GeneratedCode(
            title=f"Drop unexpected column {issue.column}",
            language="pyspark",
            code=f'df = df.drop("{issue.column}")',
            related_checks=[issue.check],
        )
    return None


def dedupe_snippets(snippets: list[GeneratedCode]) -> list[GeneratedCode]:
    seen: set[tuple[str, str]] = set()
    result: list[GeneratedCode] = []
    for snippet in snippets:
        key = (snippet.title, snippet.language)
        if key in seen:
            continue
        seen.add(key)
        result.append(snippet)
    return result


def spark_date_format(value: str) -> str:
    return (
        value.replace("%Y", "yyyy")
        .replace("%m", "MM")
        .replace("%d", "dd")
        .replace("%H", "HH")
        .replace("%M", "mm")
        .replace("%S", "ss")
    )


def bound_value(value: str) -> str:
    return value.replace(">=", "").replace("<=", "").strip()
