# Data Model

This document describes the main output objects returned by DataContract Guard.

---

## ValidationReport

The main response object.

```json
{
  "status": "FAIL",
  "sourceName": "customers",
  "counts": {},
  "issues": [],
  "corrections": [],
  "analysis": {},
  "recommendations": [],
  "generatedCode": {},
  "agent": {},
  "trace": {},
  "cost": {}
}
```

---

## Status

| Status | Meaning |
|---|---|
| `PASS` | No blocking issue detected |
| `FAIL` | At least one blocking issue detected |
| `WARNING` | Non-blocking issues detected, if supported |

---

## Counts

```json
{
  "issues": 5,
  "critical": 1,
  "high": 2,
  "medium": 2,
  "low": 0
}
```

---

## Issue

```json
{
  "severity": "CRITICAL",
  "type": "MISSING_COLUMN",
  "column": "email",
  "message": "Required column email is missing",
  "suggestion": "Column mail may be a rename candidate"
}
```

### Issue Fields

| Field | Description |
|---|---|
| `severity` | Issue severity |
| `type` | Machine-readable issue type |
| `column` | Related column when applicable |
| `message` | Human-readable message |
| `suggestion` | Suggested remediation |

---

## Severity Levels

| Severity | Meaning |
|---|---|
| `CRITICAL` | Must block ingestion |
| `HIGH` | Strong risk of pipeline or business impact |
| `MEDIUM` | Should be reviewed |
| `LOW` | Informational or low-risk issue |
| `INFO` | Useful information |

---

## Common Issue Types

```text
MISSING_COLUMN
EXTRA_COLUMN
POSSIBLE_RENAME
TYPE_MISMATCH
INVALID_DATE_FORMAT
NULL_REQUIRED_VALUE
REGEX_VALIDATION_FAILED
ALLOWED_VALUES_FAILED
MIN_VALUE_FAILED
MAX_VALUE_FAILED
```

---

## Analysis

The analysis section provides a natural language explanation.

```json
{
  "summary": "The dataset does not respect the current contract.",
  "problems": [
    "The required column email is missing",
    "The column mail may be an unannounced rename"
  ],
  "probableCauses": [
    "Producer-side schema change"
  ],
  "impacts": [
    "Spark ingestion may fail",
    "Downstream joins may be affected"
  ],
  "correctionPlan": [
    "Confirm rename with producer",
    "Rename mail to email before ingestion"
  ]
}
```

---

## Generated Code

```json
{
  "pyspark": "df = df.withColumnRenamed('mail', 'email')"
}
```

Generated code should be treated as a remediation proposal, not an automatic production action.

---

## Agent Steps

```json
{
  "steps": [
    {
      "agent": "ContractAgent",
      "action": "parse_contract",
      "status": "success"
    },
    {
      "agent": "SchemaAgent",
      "action": "infer_schema",
      "status": "success"
    },
    {
      "agent": "QualityAgent",
      "action": "run_quality_checks",
      "status": "success"
    }
  ]
}
```

---

## Trace

```json
{
  "traceId": "val-20260517-001",
  "startedAt": "2026-05-17T10:00:00Z",
  "finishedAt": "2026-05-17T10:00:02Z",
  "durationMs": 2000
}
```

---

## Cost

When LLM features are enabled:

```json
{
  "llmEnabled": true,
  "provider": "openai",
  "inputTokens": 1200,
  "outputTokens": 450,
  "estimatedCost": 0.0021
}
```
