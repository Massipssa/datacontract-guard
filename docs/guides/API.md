# API

DataContract Guard exposes a FastAPI application for validating uploaded data files against YAML contracts.

---

## Start the API

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8093 --reload
```

Open the interactive documentation:

```text
http://127.0.0.1:8093/docs
```

---

## Health Check

```http
GET /health
```

Example response:

```json
{
  "status": "ok"
}
```

---

## Validate Uploaded Data

```http
POST /validate
```

### Request

Multipart form fields:

| Field | Type | Required | Description |
|---|---|---:|---|
| `data_file` | file | yes | CSV, JSON, or Parquet file to validate |
| `contract_file` | file | yes | YAML data contract |
| `source_name` | string | no | Logical source or dataset name |

### curl Example

```bash
curl -X POST http://127.0.0.1:8093/validate \
  -F "data_file=@examples/customers_bad.csv" \
  -F "contract_file=@examples/customers_contract.yaml" \
  -F "source_name=customers"
```

---

## Example Response

```json
{
  "status": "FAIL",
  "sourceName": "customers",
  "counts": {
    "issues": 5,
    "critical": 1,
    "high": 2,
    "medium": 2,
    "low": 0
  },
  "issues": [
    {
      "severity": "CRITICAL",
      "type": "MISSING_COLUMN",
      "column": "email",
      "message": "Required column email is missing",
      "suggestion": "Column mail may be a rename candidate"
    }
  ],
  "analysis": {
    "summary": "The dataset does not respect the expected contract.",
    "probableCauses": [
      "Producer-side schema rename from email to mail"
    ],
    "impacts": [
      "Ingestion may fail",
      "Downstream joins may be affected",
      "PII controls may be bypassed"
    ],
    "correctionPlan": [
      "Confirm whether mail replaces email",
      "Rename mail to email before ingestion",
      "Update contract if the change is intentional"
    ]
  },
  "generatedCode": {
    "pyspark": "df = df.withColumnRenamed('mail', 'email')"
  }
}
```

---

## Response Fields

| Field | Description |
|---|---|
| `status` | `PASS` or `FAIL` |
| `sourceName` | Dataset or source name |
| `counts` | Issue counters by severity |
| `issues` | Technical validation issues |
| `corrections` | Suggested remediation actions |
| `analysis` | Human-readable explanation and impact |
| `recommendations` | Recommended next actions |
| `generatedCode` | Generated remediation code |
| `agent.steps` | Agent execution trace |
| `trace` | Request trace metadata |
| `cost` | Optional LLM cost metadata |

---

## Recommended Future Endpoints

For a SaaS or enterprise version:

```text
POST /contracts
GET  /contracts/{id}
POST /validations
GET  /validations/{id}
GET  /validations/{id}/report
POST /validations/{id}/generate-fix
POST /validations/{id}/generate-provider-message
```
