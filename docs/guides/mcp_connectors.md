<!-- copied from docs/MCP_CONNECTORS.md -->

# MCP Connectors — Guide and example adapter

This guide describes how to use MCP (Managed Connector Proxy) servers with DataContract Guard and provides a minimal adapter contract to implement connectors or to call MCP endpoints.

Purpose

- MCP servers expose a small, consistent API to interact with third-party systems: Git repos (contracts), object stores (incoming files), databases (schema/catalog), and issue/alerting services (Slack/Jira).
- The agent code calls MCP endpoints rather than implementing each protocol directly.

Recommended MCP API surface (example)

- GET /contracts?repo=<repo>&path=<path>
  - returns: list of contract file metadata and content
- GET /objects?bucket=<bucket>&prefix=<prefix>
  - returns: list of incoming files with presigned URLs or internal object ids
- GET /schema?datasource=<name>&table=<table>
  - returns: schema JSON compatible with `contract_agent` `Schema` model
- POST /alerts
  - body: { "channel": "slack:#alerts", "title": "DataContract guard", "text": "..." }

Example adapter interface (Python)

Place adapters under `contract_agent/adapters/mcp_adapter.py`.

```python
from typing import Protocol, Iterable
from pathlib import Path

class ContractFile(Protocol):
    path: str
    content: str

class MCPAdapter(Protocol):
    def list_contracts(self, repo: str, path: str) -> Iterable[ContractFile]:
        ...

    def list_objects(self, bucket: str, prefix: str) -> list[dict]:
        ...

    def get_schema(self, datasource: str, table: str) -> dict:
        ...

    def create_alert(self, channel: str, title: str, message: str) -> dict:
        ...
```

Integration points in DataContract Guard

- Replace direct connector calls with an adapter instance created at startup from configuration (env var `DATA_CONTRACT_MCP_URL` or local adapters if MCP is not available).
- The orchestrator or `enterprise.runtime` should accept an `mcp_adapter` optional parameter and pass it to agents that need external data (e.g., `SchemaAgent`, `ReportGeneratorAgent`).

Deployment examples

- Kubernetes: deploy MCP servers as internal services; configure the agent via `DATA_CONTRACT_MCP_URL=http://mcp.cluster.svc`.
- On-prem: run MCP as a small Flask/FastAPI service with corporate credentials for Git/S3/DB access.

Notes on fallback

- If MCP is unavailable, the adapter should fall back to local connectors implemented in `contract_agent/adapters/`.
- Keep the business logic independent from transport: implement thin adapters that return the same structures either way.
