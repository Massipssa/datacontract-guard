from __future__ import annotations

import json
from typing import Any

from contract_agent.core.models import ContractReport


def render_json(report: ContractReport) -> str:
    return json.dumps(report.as_dict(), ensure_ascii=False, indent=2)


def render_markdown(
    report: ContractReport,
    analysis: dict[str, Any] | None = None,
    generated_code: list[dict[str, Any]] | None = None,
) -> str:
    payload = report.as_dict()
    lines = [
        f"# Data Contract Report: {payload['contract']}",
        "",
        f"- Source: `{payload['source']}`",
        f"- Status: `{payload['status']}`",
        f"- Failures: `{payload['counts']['FAIL']}`",
        f"- Warnings: `{payload['counts']['WARN']}`",
        "",
    ]
    if analysis:
        lines.extend(
            [
                "## Agent Analysis",
                "",
                f"- Dataset: `{analysis['dataset']}`",
                f"- Statut: `{analysis['status']}`",
                f"- Résumé: {analysis['summary']}",
                "",
                "### Problèmes détectés",
                "",
            ]
        )
        lines.extend([f"- {item}" for item in analysis["problems"]] or ["- Aucun problème détecté."])
        lines.extend(["", "### Impact", ""])
        lines.extend([f"- {item}" for item in analysis["impacts"]] or ["- Aucun impact identifié."])
        lines.extend(["", "### Correction proposée", ""])
        lines.extend([f"- {item}" for item in analysis["correctionPlan"]] or ["- Aucune correction nécessaire."])
        lines.append("")

    lines.extend(["## Issues", ""])
    if not payload["issues"]:
        lines.append("No issue detected.")
    else:
        for issue in payload["issues"]:
            lines.append(
                f"- **{issue['severity']}** `{issue['check']}` on `{issue['column']}`: {issue['message']}"
            )
            if "expected" in issue or "actual" in issue:
                lines.append(f"  - expected: `{issue.get('expected')}`")
                lines.append(f"  - actual: `{issue.get('actual')}`")
            if "row" in issue:
                lines.append(f"  - row: `{issue['row']}`")
            if "impact" in issue:
                lines.append(f"  - impact: {issue['impact']}")
    lines.extend(["", "## Proposed Corrections", ""])
    if not payload["corrections"]:
        lines.append("No correction needed.")
    else:
        for correction in payload["corrections"]:
            lines.append(
                f"- `{correction['action']}` on `{correction['target']}`: {correction['suggestion']}"
            )
    if generated_code:
        lines.extend(["", "## Generated Code", ""])
        for snippet in generated_code:
            lines.append(f"### {snippet['title']}")
            lines.append("")
            lines.append(f"```{snippet['language']}")
            lines.append(str(snippet["code"]))
            lines.append("```")
            lines.append("")
    return "\n".join(lines)
