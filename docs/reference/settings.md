<!-- copied from docs/SETTINGS.md -->

**Settings and Environment Configuration**

This project uses a small `Settings` dataclass to centralize runtime configuration.
Settings are normally created with `Settings.from_env(base_dir)` which reads
environment variables and derives sensible defaults.

Key environment variables

- `DATA_CONTRACT_ENV` — runtime environment (default: `local`).
- `DATA_CONTRACT_ALLOWED_ROOTS` — semicolon-separated list of filesystem roots the agent may read.
- `DATA_CONTRACT_API_KEY` — optional API key for the HTTP API.
- `DATA_CONTRACT_LOG_LEVEL` — log level (default: `INFO`).
- `DATA_CONTRACT_MAX_DATA_ROWS` — maximum rows to validate when reading sample data.
- `DATA_CONTRACT_DOCS_PATH` — path to project documentation used by the `DocumentRetriever`.
- `DATA_CONTRACT_ENABLE_VECTOR_STORE` — `true|false` to enable the optional Chroma vector store.
- `DATA_CONTRACT_VECTOR_STORE_PATH` — path where the Chroma vector store will persist.
- `DATA_CONTRACT_MCP_URL` — base URL of your MCP (Managed Connector Proxy) service. When set, an `MCPAdapter` is created and passed to agents.
- `DATA_CONTRACT_MCP_TOKEN` — Bearer token used when calling the MCP API. If provided, the `MCPAdapter` will include `Authorization: Bearer <token>` on requests.

Example: run the CLI against an MCP service

PowerShell example (token in env):

```powershell
$env:DATA_CONTRACT_MCP_URL = 'https://mcp.internal.example'
$env:DATA_CONTRACT_MCP_TOKEN = 's3cr3t-token'
python -B -m contract_agent.cli `
  --source-schema 'datasource.table' `
  --contract 'repo:contracts/customer_contract.yaml'
```

Notes

- `DATA_CONTRACT_MCP_URL` and `DATA_CONTRACT_MCP_TOKEN` are optional. When
  present, the runtime will create an `MCPAdapter` and pass it to the
  orchestrator so agents can fetch contracts, schemas, bucket objects, or
  create alerts through your MCP.
- If you enable `DATA_CONTRACT_ENABLE_VECTOR_STORE`, install the optional
  extras and ensure `chromadb` and a sentence embedding model are available.

Where the settings live

The `Settings` dataclass is implemented in `contract_agent/enterprise/settings.py`.
Call `Settings.from_env(Path(__file__).parent)` in your application entrypoint
to construct runtime settings from environment variables.
