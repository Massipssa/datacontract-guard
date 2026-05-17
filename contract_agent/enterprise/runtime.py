from __future__ import annotations

import logging
from dataclasses import dataclass

from contract_agent.agents.orchestrator import AgentOrchestrator, AgentRun, AgentRunRequest
from contract_agent.core.models import ContractReport
from contract_agent.enterprise.costs import CostSummary, enforce_budget
from contract_agent.enterprise.logging import log_event
from contract_agent.enterprise.security import resolve_allowed_path
from contract_agent.enterprise.settings import Settings
from contract_agent.enterprise.tracing import Trace


@dataclass(frozen=True)
class EvaluationResult:
    report: ContractReport
    trace: Trace
    cost: CostSummary
    agent: AgentRun

    def as_dict(self) -> dict:
        payload = self.report.as_dict()
        payload["analysis"] = self.agent.analysis
        payload["recommendations"] = self.agent.recommendations
        payload["generatedCode"] = self.agent.generated_code
        payload["llmExplanation"] = self.agent.llm_explanation
        payload["agent"] = self.agent.as_dict()
        payload["trace"] = self.trace.as_dict()
        payload["cost"] = self.cost.as_dict()
        return payload


def evaluate_files(
    source_schema_path: str,
    contract_path: str,
    settings: Settings,
    source_name: str | None = None,
    allow_safe_promotion: bool = True,
    warn_extra_columns: bool = True,
    data_path: str | None = None,
    validate_data: bool = True,
) -> EvaluationResult:
    logger = logging.getLogger("data_contract_agent")
    trace = Trace()
    source_path = resolve_allowed_path(source_schema_path, settings)
    contract_resolved_path = resolve_allowed_path(contract_path, settings)
    data_resolved_path = resolve_allowed_path(data_path, settings) if data_path and validate_data else None
    trace.span(
        "paths.resolved",
        source=str(source_path),
        contract=str(contract_resolved_path),
        data=str(data_resolved_path) if data_resolved_path else None,
    )

    agent_run = AgentOrchestrator().run(
        AgentRunRequest(
            source_path=source_path,
            contract_path=contract_resolved_path,
            source_name=source_name,
            data_path=data_resolved_path,
            validate_data=validate_data,
            max_data_rows=settings.max_data_rows,
            allow_safe_promotion=allow_safe_promotion,
            warn_extra_columns=warn_extra_columns,
        )
    )
    trace.span(
        "agent.orchestrated",
        stepCount=len(agent_run.steps),
        status=agent_run.report.status,
        rowCount=agent_run.row_count,
    )
    for step in agent_run.steps:
        trace.span(
            "agent.step",
            agent=step.name,
            status=step.status,
            summary=step.summary,
        )

    cost = enforce_budget(agent_run.source_schema, agent_run.contract, settings, data_rows=agent_run.row_count)
    trace.span("budget.checked", estimatedUnits=cost.estimated_units)
    report = agent_run.report
    trace.span("contract.evaluated", status=report.status, issueCount=len(report.issues))
    log_event(
        logger,
        logging.INFO,
        "contract_evaluated",
        traceId=trace.trace_id,
        status=report.status,
        source=agent_run.source_schema.name,
        contract=agent_run.contract.name,
    )
    trace.span("analysis.generated", problemCount=len(agent_run.analysis["problems"]))
    return EvaluationResult(report=report, trace=trace, cost=cost, agent=agent_run)
