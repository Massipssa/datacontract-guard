from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from contract_agent.agents.base import AgentStep, ok_step
from contract_agent.agents.code_generator import CodeGeneratorAgent, GeneratedCode
from contract_agent.core.data_quality import merge_reports
from contract_agent.core.explainer import explain_report
from contract_agent.core.models import ContractReport


@dataclass(frozen=True)
class ReportAgentResult:
    report: ContractReport
    analysis: dict[str, Any]
    recommendations: list[str]
    generated_code: list[GeneratedCode]
    step: AgentStep


class ReportGeneratorAgent:
    name = "Report Generator"

    def build(
        self,
        schema_report: ContractReport,
        quality_report: ContractReport | None,
    ) -> ReportAgentResult:
        report = merge_reports(schema_report, quality_report)
        analysis = explain_report(report)
        generated_code = CodeGeneratorAgent().generate(report)
        recommendations = analysis["correctionPlan"]
        step = ok_step(
            self.name,
            "Final report, recommendations, and generated code prepared.",
            status=report.status,
            problemCount=len(analysis["problems"]),
            recommendationCount=len(recommendations),
            generatedCodeCount=len(generated_code),
        )
        return ReportAgentResult(
            report=report,
            analysis=analysis,
            recommendations=recommendations,
            generated_code=generated_code,
            step=step,
        )
