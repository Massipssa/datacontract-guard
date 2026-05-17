from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import os
from pathlib import Path

from contract_agent.agents.base import AgentStep, ok_step
from contract_agent.agents.code_generator import CodeGeneratorAgent, GeneratedCode
from contract_agent.agents.llm_explanation_agent import LLMExplanation, LLMExplanationAgent
try:
    from contract_agent.agents.document_retriever import DocumentRetriever  # type: ignore
except Exception:
    DocumentRetriever = None
from contract_agent.core.data_quality import merge_reports
from contract_agent.core.explainer import explain_report
from contract_agent.core.models import ContractReport


@dataclass(frozen=True)
class ReportAgentResult:
    report: ContractReport
    analysis: dict[str, Any]
    recommendations: list[str]
    generated_code: list[GeneratedCode]
    llm_explanation: LLMExplanation
    steps: list[AgentStep]


class ReportGeneratorAgent:
    name = "Report Generator"

    def build(
        self,
        schema_report: ContractReport,
        quality_report: ContractReport | None,
        mcp_adapter: Any | None = None,
    ) -> ReportAgentResult:
        report = merge_reports(schema_report, quality_report)
        analysis = explain_report(report)
        generated_code = CodeGeneratorAgent().generate(report)
        recommendations = analysis["correctionPlan"]
        report_payload = report.as_dict()
        report_payload["analysis"] = analysis
        report_payload["recommendations"] = recommendations
        report_payload["generatedCode"] = [snippet.as_dict() for snippet in generated_code]
        # instantiate an optional document retriever from environment variables
        retriever = None
        try:
            if DocumentRetriever is not None:
                docs_path = os.environ.get("DATA_CONTRACT_DOCS_PATH", str(Path(__file__).resolve().parents[2] / "docs"))
                persist_path = os.environ.get("DATA_CONTRACT_VECTOR_STORE_PATH", str(Path(__file__).resolve().parents[2] / ".chroma_store"))
                retriever = DocumentRetriever(Path(docs_path), Path(persist_path))
        except Exception:
            retriever = None

        # pass MCP adapter to explanation agent so it can emit alerts or fetch extra content if needed
        llm_result = LLMExplanationAgent(retriever=retriever).generate(report_payload)
        report_step = ok_step(
            self.name,
            "Final report, recommendations, generated code, and LLM explanation prepared.",
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
            llm_explanation=llm_result.explanation,
            steps=[report_step, llm_result.step],
        )
