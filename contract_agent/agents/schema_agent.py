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

    def infer(self, source_path: Path | str, source_name: str | None = None, mcp_adapter: Any | None = None) -> SchemaAgentResult:
        # If source_path is a string and MCP adapter is available, attempt to fetch schema from MCP
        if isinstance(source_path, str) and mcp_adapter is not None:
            try:
                # expect source_path like 'datasource.table' or similar
                parts = source_path.split(".", 1)
                datasource = parts[0]
                table = parts[1] if len(parts) > 1 else ""
                payload = mcp_adapter.get_schema(datasource, table)
                # payload expected to be JSON schema compatible with read_json_schema
                # create a temporary JSON-style object
                from contract_agent.core.models import Schema as _Schema, Column as _Column

                columns = [
                    _Column(name=col.get("name"), type=col.get("type", "string")) for col in payload.get("columns", [])
                ]
                schema = _Schema(name=payload.get("name", source_name or datasource), columns=columns)
            except Exception:
                # fallback to local reader behavior if MCP fails
                schema = read_source_schema(Path(source_path) if isinstance(source_path, str) else source_path, source_name)
        else:
            schema = read_source_schema(source_path if isinstance(source_path, Path) else Path(str(source_path)), source_name)
        step = ok_step(
            self.name,
            "Schema inferred from the received source.",
            source=str(source_path),
            sourceName=schema.name,
            columnCount=len(schema.columns),
            columns=[column.name for column in schema.columns],
        )
        return SchemaAgentResult(schema=schema, step=step)
