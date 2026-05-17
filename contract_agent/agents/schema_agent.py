from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from contract_agent.adapters.schema_reader import read_source_schema
from contract_agent.agents.base import AgentStep, ok_step
from contract_agent.core.models import Schema


@dataclass(frozen=True)
class SchemaAgentResult:
    schema: Schema
    step: AgentStep


class SchemaAgent:
    name = "Schema Agent"

    def infer(self, source_path: Path, source_name: str | None = None) -> SchemaAgentResult:
        schema = read_source_schema(source_path, source_name)
        step = ok_step(
            self.name,
            "Schema inferred from the received source.",
            source=str(source_path),
            sourceName=schema.name,
            columnCount=len(schema.columns),
            columns=[column.name for column in schema.columns],
        )
        return SchemaAgentResult(schema=schema, step=step)
