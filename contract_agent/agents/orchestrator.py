from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from contract_agent.agents.base import AgentStep, ok_step
from contract_agent.agents.contract_agent import ContractAgent
from contract_agent.agents.quality_agent import QualityAgent
from contract_agent.agents.report_agent import ReportGeneratorAgent
from contract_agent.agents.schema_agent import SchemaAgent
from contract_agent.core.models import ContractReport, DataContract, Schema


@dataclass(frozen=True)
class AgentRun:
    report: ContractReport
    analysis: dict[str, Any]
    recommendations: list[str]
    generated_code: list[dict[str, object]]
    llm_explanation: dict[str, str]
    steps: list[AgentStep]
    source_schema: Schema
    contract: DataContract
    row_count: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": "Agent IA Data Quality / Data Contract",
            "mode": "orchestrated_multi_agent",
            "steps": [step.as_dict() for step in self.steps],
            "analysis": self.analysis,
            "recommendations": self.recommendations,
            "generatedCode": self.generated_code,
            "llmExplanation": self.llm_explanation,
        }


@dataclass(frozen=True)
class AgentRunRequest:
    source_path: Path | str
    contract_path: Path | str
    source_name: str | None = None
    data_path: Path | None = None
    validate_data: bool = True
    max_data_rows: int = 1000
    allow_safe_promotion: bool = True
    warn_extra_columns: bool = True
    mcp_adapter: Any | None = None


class AgentOrchestrator:
    name = "Agent Orchestrator"

    def run(self, request: AgentRunRequest) -> AgentRun:
        steps: list[AgentStep] = [
            ok_step(
                self.name,
                "User request accepted and routed to specialized agents.",
                source=str(request.source_path),
                contract=str(request.contract_path),
                validateData=request.validate_data,
            )
        ]

        schema_result = SchemaAgent().infer(request.source_path, request.source_name, mcp_adapter=request.mcp_adapter)
        steps.append(schema_result.step)

        contract_agent = ContractAgent()
        contract_result = contract_agent.load(request.contract_path, mcp_adapter=request.mcp_adapter)
        steps.append(contract_result.step)

        schema_comparison = contract_agent.compare(
            schema_result.schema,
            contract_result.contract,
            allow_safe_promotion=request.allow_safe_promotion,
            warn_extra_columns=request.warn_extra_columns,
        )
        steps.append(schema_comparison.step)

        data_path = request.data_path
        if data_path is None and request.validate_data and request.source_path.suffix.lower() in {".csv", ".parquet"}:
            data_path = request.source_path

        quality_result = QualityAgent().run(
            data_path if request.validate_data else None,
            contract_result.contract,
            schema_result.schema.name,
            request.max_data_rows,
        )
        steps.append(quality_result.step)

        report_result = ReportGeneratorAgent().build(schema_comparison.report, quality_result.report, mcp_adapter=request.mcp_adapter)
        steps.extend(report_result.steps)

        return AgentRun(
            report=report_result.report,
            analysis=report_result.analysis,
            recommendations=report_result.recommendations,
            generated_code=[snippet.as_dict() for snippet in report_result.generated_code],
            llm_explanation=report_result.llm_explanation.as_dict(),
            steps=steps,
            source_schema=schema_result.schema,
            contract=contract_result.contract,
            row_count=len(quality_result.rows),
        )
