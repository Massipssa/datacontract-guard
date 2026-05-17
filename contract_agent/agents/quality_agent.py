from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from contract_agent.adapters.schema_reader import read_data_rows
from contract_agent.agents.base import AgentStep, ok_step
from contract_agent.core.data_quality import DataQualityAgent
from contract_agent.core.models import ContractReport, DataContract


@dataclass(frozen=True)
class QualityAgentResult:
    rows: list[dict[str, Any]]
    report: ContractReport | None
    step: AgentStep


class QualityAgent:
    name = "Quality Agent"

    def run(
        self,
        data_path: Path | None,
        contract: DataContract,
        source_name: str,
        max_rows: int,
    ) -> QualityAgentResult:
        if data_path is None:
            return QualityAgentResult(
                rows=[],
                report=None,
                step=ok_step(self.name, "No row-level data sample was provided.", rowCount=0),
            )

        rows = read_data_rows(data_path, limit=max_rows + 1)
        report = DataQualityAgent().evaluate_rows(rows, contract, source_name)
        step = ok_step(
            self.name,
            "Row-level data quality checks executed.",
            data=str(data_path),
            rowCount=len(rows),
            status=report.status,
            issueCount=len(report.issues),
            correctionCount=len(report.corrections),
        )
        return QualityAgentResult(rows=rows, report=report, step=step)
