# DataContract Guard

Validate incoming data before it breaks your pipelines.

**DataContract Guard** is an AI-assisted data quality and data contract guardrail for data engineers.  
It validates CSV, JSON, Parquet, and contract metadata before data is appended to Spark, warehouse, or Iceberg pipelines.

> Detect schema drift, understand the impact, and get a remediation plan before ingestion.

---

## Why DataContract Guard?

Classic validators stop at technical errors such as:

```text
Column email is missing.
```

DataContract Guard goes further:

```text
The required column "email" is missing.
A similar column "mail" is present.
This is probably an unversioned producer-side rename.
Impact: Spark/Iceberg writes, joins, dashboards, and PII controls may be affected.
Recommended action: rename mail to email or update the contract if the change is intentional.
```

The deterministic engine remains the source of truth for `PASS` / `FAIL`.  
The agent layer explains, prioritizes, and recommends.

---

## What It Does

- Validates source schemas against YAML data contracts
- Infers schemas from CSV files
- Supports Parquet when `pyarrow` is installed
- Detects missing, extra, renamed, and incompatible columns
- Validates required fields, date formats, regex patterns, allowed values, min/max rules
- Generates JSON or Markdown reports
- Produces remediation suggestions and PySpark code
- Provides CLI, API, Docker, and CI/CD usage

---

## Architecture

```text
User / API / CLI
      ↓
Agent Orchestrator
      ├── Schema Agent
      ├── Contract Agent
      ├── Quality Agent
      ├── LLM Explanation Agent
      └── Report Generator
      ↓
Validation Report + Recommendations + PySpark Fix
```

More details: [Architecture](docs/ARCHITECTURE.md)

---

## Quick Start

Run a contract validation:

```bash
python -B -m contract_agent.cli \
  --source-schema examples/source_schema.json \
  --contract examples/customer_contract.yaml
```

Generate JSON output:

```bash
python -B -m contract_agent.cli \
  --source-schema examples/source_schema.json \
  --contract examples/customer_contract.yaml \
  --output json
```

Validate a received CSV file:

```bash
python -B -m contract_agent.cli \
  --source-schema examples/customers_bad.csv \
  --contract examples/customers_contract.yaml \
  --source-name customers
```

Expected result: the report fails because the received file does not respect the contract.

---

## Example

Input file:

```csv
customer_id,mail,birth_date,amount
,test@gmail.com,01/01/1990,25.5
,second@gmail.com,1990-01-02,-3
789,third@gmail.com,1990-02-03,-1
```

Expected contract:

```yaml
columns:
  - name: customer_id
    type: long
    required: true

  - name: email
    type: string
    required: true

  - name: birth_date
    type: date
    required: true
    format: "%Y-%m-%d"

  - name: amount
    type: double
    required: true
    min: 0
```

Detected issues:

```text
Status: FAIL

Problems:
- Required column "email" is missing
- Similar column "mail" is present
- birth_date contains invalid format
- customer_id contains empty required values
- amount contains values below 0
```

Generated remediation example:

```python
from pyspark.sql.functions import col, trim, to_date

# Rename likely producer-side column rename
df = df.withColumnRenamed("mail", "email")

# Convert date format
df = df.withColumn("birth_date", to_date(col("birth_date"), "yyyy-MM-dd"))

# Split valid and invalid records
valid_customer_id = df.filter(
    col("customer_id").isNotNull() & (trim(col("customer_id")) != "")
)

valid_amount = valid_customer_id.filter(col("amount") >= 0)
invalid_amount = valid_customer_id.filter(col("amount") < 0)
```

---

## API Usage

Start the FastAPI application:

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8093 --reload
```

Validate an uploaded file:

```bash
curl -X POST http://127.0.0.1:8093/validate \
  -F "data_file=@examples/customers_bad.csv" \
  -F "contract_file=@examples/customers_contract.yaml" \
  -F "source_name=customers"
```

The API returns a `ValidationReport` containing:

- `status`
- `counts`
- `issues`
- `corrections`
- `analysis`
- `recommendations`
- `generatedCode`
- `agent.steps`
- `trace`
- `cost`

More details: [API](docs/API.md)

---

## Docker

Run the containerized API:

```bash
docker compose up --build
```

The API is exposed on:

```text
http://127.0.0.1:8093
```

---

## CI/CD Gate

DataContract Guard can be used as a CI gate.

```bash
python -B -m contract_agent.cli \
  --source-schema examples/source_schema.json \
  --contract examples/customer_contract.yaml \
  --output json
```

Exit code is `1` when the report status is `FAIL`.

More details: [CI/CD Integration](docs/CI_CD.md)

---

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Data Model](docs/DATA_MODEL.md)
- [Settings](docs/SETTINGS.md)
- [API](docs/API.md)
- [CLI Usage](docs/CLI.md)
- [Contract Format](docs/CONTRACT_FORMAT.md)
- [Source Schema Format](docs/SOURCE_SCHEMA_FORMAT.md)
- [Enterprise Guardrails](docs/ENTERPRISE_GUARDRAILS.md)
- [CI/CD Integration](docs/CI_CD.md)
- [Airflow Integration](docs/AIRFLOW.md)
- [LLM Explanation Agent](docs/LLM_EXPLANATION.md)
- [RAG](docs/RAG.md)
- [MCP Connectors](docs/MCP_CONNECTORS.md)
- [Examples](docs/EXAMPLES.md)
- [Evaluation](docs/EVALUATION.md)

---

## Tests

```bash
python -B -m unittest discover -s tests
```

Run golden evaluation cases:

```bash
python -B -m contract_agent.evaluation --eval-file examples/evaluation_cases.json
```

---

## Roadmap

- Streamlit or React demo UI
- GitHub / GitLab contract integration
- S3 and Glue Catalog integration
- Iceberg schema compatibility checks
- RAG-based documentation enrichment
- Model Context Protocol integration
- SaaS workspace and validation history

---

## Positioning

DataContract Guard is not just a schema validator.

It is an AI-assisted guardrail that helps data teams:

- detect contract violations early;
- understand producer-side schema drift;
- explain business and technical impact;
- generate remediation code;
- prevent broken pipelines before ingestion.
