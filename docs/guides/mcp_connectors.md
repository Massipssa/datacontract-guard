# MCP Connectors

This document describes how DataContract Guard can evolve toward connector-based integrations.

---

## Important Naming Note

In modern AI systems, MCP usually means **Model Context Protocol**.

Avoid using MCP to mean another internal concept such as “Managed Connector Proxy”, because it can create confusion.

Recommended terms:

- `Connector Gateway`
- `Data Connector Proxy`
- `Integration Layer`
- Or adopt the real Model Context Protocol standard

---

## Why Connectors?

A production data contract agent should connect to systems where data and contracts live.

Useful integrations:

- GitHub / GitLab for contracts
- S3 for incoming files
- PostgreSQL / Snowflake / BigQuery for schemas
- AWS Glue Catalog for metadata
- Iceberg Catalog for table schemas
- Slack / Teams for alerts
- Jira for issue creation

---

## Connector-Based Flow

```text
User asks: validate customers dataset
        ↓
Agent Orchestrator
        ↓
Connector: GitHub/GitLab → read contract YAML
        ↓
Connector: S3 → read latest incoming file
        ↓
Validation Engine
        ↓
Connector: Slack/Jira → notify or create issue
```

---

## Example Connector Interface

```python
class ContractRepository:
    def get_contract(self, dataset_name: str, version: str | None = None) -> str:
        raise NotImplementedError


class DataSourceRepository:
    def get_latest_sample(self, dataset_name: str) -> bytes:
        raise NotImplementedError
```

---

## Future Model Context Protocol Integration

With MCP, the agent could use external MCP servers such as:

```text
MCP GitHub Server
MCP Filesystem Server
MCP PostgreSQL Server
MCP Slack Server
MCP Jira Server
```

Target architecture:

```text
DataContract Guard Agent
        ↓
MCP Client
        ↓
MCP Servers
        ├── GitHub
        ├── S3 / Filesystem
        ├── PostgreSQL
        ├── Slack
        └── Jira
```

---

## Security Recommendations

- Use read-only access by default
- Require approval before creating tickets or sending alerts
- Never expose credentials to the LLM
- Scope connector permissions per workspace
- Log connector calls with trace IDs
