# Data Contract Agent

Validate a source schema against a YAML data contract before a pipeline publishes
breaking changes.

This project is designed for data engineers who want a usable enterprise
guardrail in CI, Airflow, ingestion jobs, API workflows, or pre-deployment
checks.

The agent does more than technical validation:

1. it checks received data against the expected contract;
2. it connects weak signals, such as `email` missing while `mail` is present;
3. it explains the likely cause, business impact, and correction plan.

## Functional Architecture

```text
User / API
   |
   v
Agent Orchestrator
   |
   +--> Schema Agent   --> Infer Schema
   +--> Quality Agent  --> Run row-level checks
   +--> Contract Agent --> Compare YAML contract
   |
   v
Report Generator
   |
   v
Report + recommendations + generated PySpark code
```

The runtime is intentionally split into agents:

- `Agent Orchestrator`: routes the request and keeps the execution trace;
- `Schema Agent`: infers the real schema from CSV, JSON, or Parquet;
- `Contract Agent`: loads the YAML contract and detects schema drift;
- `Quality Agent`: validates nulls, formats, patterns, domains, and business rules;
- `Report Generator`: merges findings, explains impact, recommends fixes, and generates code.

## What It Does

- reads a source schema from JSON;
- infers a schema from a CSV sample;
- infers a schema from Parquet when optional `pyarrow` is installed;
- reads a YAML data contract;
- detects missing columns;
- detects renamed columns;
- detects incompatible type changes;
- detects extra source columns;
- detects empty required values;
- detects invalid date and timestamp formats;
- detects invalid values with patterns or allowed value lists;
- detects numeric business rules such as `min` and `max`;
- explains probable causes and business impact;
- proposes corrections;
- generates JSON or Markdown reports.

## Project Tree

```text
data-contract-agent/
  contract_agent/
    agents/
      orchestrator.py   functional agent orchestration
      schema_agent.py   source schema inference agent
      quality_agent.py  row-level data quality agent
      contract_agent.py contract loading and comparison agent
      report_agent.py   final report and recommendations agent
      code_generator.py PySpark remediation snippets
    core/
      agent.py          contract comparison use case
      data_quality.py   row-level quality checks
      explainer.py      agent-style cause, impact, and fix analysis
      contract.py       contract model mapping
      models.py         schemas, issues, corrections, reports
      reporting.py      JSON and Markdown rendering
    adapters/
      mini_yaml.py      small dependency-free YAML parser
      schema_reader.py  JSON/CSV source schema readers
    enterprise/
      costs.py          budget and cost estimates
      logging.py        JSON logs
      runtime.py        guarded evaluation runtime
      security.py       API keys and path allow-listing
      settings.py       environment configuration
      tracing.py        per-request spans
    api/
      http.py           dependency-free HTTP API
    cli.py              command-line agent
    evaluation.py       response evaluation runner
  examples/
    customer_contract.yaml
    source_schema.json
    source_sample.csv
    supplier_contract.yaml
    supplier_bad.csv
    customers_contract.yaml
    customers_bad.csv
    evaluation_cases.json
  tests/
  Dockerfile
  docker-compose.yml
  pyproject.toml
```

## Get Started

From this directory:

```powershell
python -B -m contract_agent.cli `
  --source-schema .\examples\source_schema.json `
  --contract .\examples\customer_contract.yaml
```

Expected result: the report fails because:

- `customer_id` is `string` in the source but `long` in the contract;
- `signup_ts` is missing from the source;
- `created_at` and `marketing_opt_in` are extra source columns.

Generate JSON:

```powershell
python -B -m contract_agent.cli `
  --source-schema .\examples\source_schema.json `
  --contract .\examples\customer_contract.yaml `
  --output json
```

Write a Markdown report:

```powershell
python -B -m contract_agent.cli `
  --source-schema .\examples\source_schema.json `
  --contract .\examples\customer_contract.yaml `
  --report-file .\contract-report.md
```

A generated example is available at `examples/sample-report.md`.

Infer a schema from a CSV sample:

```powershell
python -B -m contract_agent.cli `
  --source-schema .\examples\source_sample.csv `
  --contract .\examples\customer_contract.yaml
```

Validate a received supplier file against the expected contract:

```powershell
python -B -m contract_agent.cli `
  --source-schema .\examples\supplier_bad.csv `
  --contract .\examples\supplier_contract.yaml `
  --source-name supplier.payment_file
```

Expected result: the report fails because:

- `email` appears to have been renamed to `mail`;
- `birth_date` uses `01/01/1990` instead of `%Y-%m-%d`;
- one `amount` value cannot be parsed as a decimal.

If your schema is stored separately from the data sample, pass both files:

```powershell
python -B -m contract_agent.cli `
  --source-schema .\examples\source_schema.json `
  --data-file .\examples\supplier_bad.csv `
  --contract .\examples\supplier_contract.yaml
```

Parquet files are supported when `pyarrow` is available in the runtime image.
Without it, the agent returns a clear configuration error.

Run the complete agent scenario:

```powershell
python -B -m contract_agent.cli `
  --source-schema .\examples\customers_bad.csv `
  --contract .\examples\customers_contract.yaml `
  --source-name customers
```

The agent explains that:

- the required `email` column is missing while a similar `mail` column exists;
- the producer probably renamed `email` to `mail`;
- `birth_date` contains a value in `01/01/1990` instead of `%Y-%m-%d`;
- `customer_id` contains empty required values;
- `amount` contains negative values while the contract declares `min: 0`;
- Spark jobs, Iceberg appends, joins on `customer_id`, finance dashboards, and
  privacy controls can be impacted.

## Contract Format

```yaml
name: customer_profile_contract
version: 1.0.0
owner: data-platform
columns:
  - name: customer_id
    type: long
    required: true
    description: Stable customer identifier
  - name: email
    type: string
    required: true
  - name: signup_ts
    type: timestamp
    required: true
    format: "%Y-%m-%dT%H:%M:%SZ"
  - name: country
    type: string
    required: false
    allowed_values: [FR, US, MA]
  - name: amount
    type: double
    required: true
    min: 0
```

The starter parser supports the simple YAML shape above. If your contracts
become more complex, replace `contract_agent/adapters/mini_yaml.py` with PyYAML
or your platform parser.

## Source Schema Format

```json
{
  "name": "bronze.customer_profile",
  "columns": [
    { "name": "customer_id", "type": "string" },
    { "name": "email", "type": "string" }
  ]
}
```

## Correction Examples

The agent can propose actions such as:

- `ADD_SOURCE_COLUMN`: add a missing required column upstream;
- `RENAME_SOURCE_COLUMN`: restore a renamed source field;
- `CAST_SOURCE_COLUMN`: cast a source column to the contract type;
- `NORMALIZE_DATE_FORMAT`: convert dates or timestamps to the expected format;
- `CAST_OR_CLEAN_VALUE`: clean values that cannot be parsed as the expected type;
- `FIX_VALUE_PATTERN`: clean values that do not match a regex pattern;
- `ENFORCE_MIN_VALUE`: reject values below a declared minimum;
- `UPDATE_CONTRACT_TYPE`: accept a safe promotion in the contract;
- `ADD_CONTRACT_COLUMN`: add an intentional new source field to the contract.

## Agent Output

Each API or JSON CLI response contains:

- `issues`: technical contract and quality findings;
- `corrections`: machine-readable actions;
- `agent.steps`: executed agents and their summaries;
- `analysis.problems`: human-readable explanation;
- `analysis.probableCauses`: inferred causes;
- `analysis.impacts`: Spark, Iceberg, BI, join, and privacy risks;
- `analysis.correctionPlan`: recommended remediation steps;
- `recommendations`: flattened action plan;
- `generatedCode`: PySpark snippets to fix or quarantine bad data.

Example explanation:

```text
La colonne obligatoire "email" est absente. Une colonne similaire "mail" est présente.
Il est probable que le producteur ait renommé "email" en "mail".
Risque que les contrôles RGPD/PII ne s'appliquent plus au bon champ.
Renommer "mail" en "email" ou mettre à jour le contrat si le changement est volontaire.
```

## CI Gate

```powershell
python -B -m contract_agent.cli `
  --source-schema .\examples\source_schema.json `
  --contract .\examples\customer_contract.yaml `
  --output json
```

Exit code is `1` when the report status is `FAIL`.

## Enterprise Guardrails

The runtime includes operational controls that make the prototype safer to run
in a real platform:

- guardrails: allowed root directories, max input file size, max request body;
- logging: JSON structured events written to stderr;
- tracing: every evaluation returns a `traceId`, elapsed time, and spans;
- response evaluation: golden cases validate expected issues and corrections;
- automated tests: `unittest` suite for core, API, guardrails, and evaluation;
- cost management: column budgets and estimated comparison units;
- secret management: API key read only from environment variables;
- tool security: API requests cannot read files outside configured roots;
- limited permissions: container runs read-only, with no extra Linux capabilities;
- API deployment: local HTTP server plus Docker Compose.

## Configuration

Use environment variables for deployment-specific controls:

```text
DATA_CONTRACT_ENV=production
DATA_CONTRACT_ALLOWED_ROOTS=/contracts;/schemas
DATA_CONTRACT_MAX_FILE_BYTES=5242880
DATA_CONTRACT_MAX_COLUMNS=500
DATA_CONTRACT_MAX_CONTRACT_COLUMNS=500
DATA_CONTRACT_MAX_DATA_ROWS=1000
DATA_CONTRACT_API_KEY=replace-with-secret-manager-value
DATA_CONTRACT_LOG_LEVEL=INFO
```

`DATA_CONTRACT_ALLOWED_ROOTS` is semicolon-separated. Relative request paths are
resolved from the first allowed root. In production, inject
`DATA_CONTRACT_API_KEY` from your secrets manager rather than committing it.

## API

Start the local API:

```powershell
python -B .\api_server.py --host 127.0.0.1 --port 8093
```

Health check:

```powershell
Invoke-RestMethod http://127.0.0.1:8093/api/health
```

Evaluate a schema against a contract:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8093/api/evaluate `
  -ContentType "application/json" `
  -Headers @{ Authorization = "Bearer $env:DATA_CONTRACT_API_KEY" } `
  -Body (Get-Content -Raw .\examples\api-evaluate-request.json)
```

The API also accepts `dataFilePath` and `validateData`:

```json
{
  "sourceSchemaPath": "examples/supplier_bad.csv",
  "contractPath": "examples/supplier_contract.yaml",
  "sourceName": "supplier.payment_file",
  "validateData": true
}
```

If `DATA_CONTRACT_API_KEY` is empty, local API authentication is disabled.

## Response Evaluation

Run golden evaluation cases:

```powershell
python -B -m contract_agent.evaluation --eval-file .\examples\evaluation_cases.json
```

The command exits with code `1` if expected statuses, issue checks, or correction
actions drift.

## API Deployment

Run the containerized API:

```powershell
docker compose up --build
```

The Compose profile binds `8093`, keeps the container filesystem read-only, uses
`/tmp` as tmpfs, drops Linux capabilities, and blocks privilege escalation.

## Airflow Integration

```python
from pathlib import Path
from contract_agent.adapters.schema_reader import read_contract, read_source_schema
from contract_agent.core.agent import DataContractAgent

contract = read_contract(Path("/contracts/customer_contract.yaml"))
source = read_source_schema(Path("/schemas/customer_profile.json"))
report = DataContractAgent().evaluate(source, contract)

if report.status == "FAIL":
    raise RuntimeError(report.as_dict())
```

## Tests

```powershell
python -B -m unittest discover -s tests
```
