<!-- copied from docs/SCHEMA.md -->

# Data Model and JSON Schema (overview)

This file documents the main data classes used by the agent and shows the JSON payload shapes used in API responses.

Models (Python dataclasses in `contract_agent/core/models.py`)

- `Column`
  - `name` (str)
  - `type` (str)
  - `required` (bool)
  - `description`, `format`, `pattern` (str)
  - `allowed_values` (list[str])
  - `min_value`, `max_value` (str)

- `Schema`
  - `name` (str)
  - `columns` (list[`Column`])

- `DataContract`
  - `name`, `version`, `owner` (str)
  - `columns` (list[`Column`])

- `ContractIssue`
  - `severity` ("FAIL"|"WARN"|"INFO")
  - `check` (e.g., `column.missing`, `value.format`)
  - `column` (str)
  - `message` (str)
  - optional `expected`, `actual`, `row`, `impact`

- `Correction`
  - `action` (str), `target` (str), `suggestion` (str)

- `ContractReport`
  - `contract` (str), `source` (str), `status` ("PASS"|"FAIL")
  - `issues` (list[`ContractIssue`])
  - `corrections` (list[`Correction`])

Example JSON response (abridged)

```json
{
  "contract": "examples/customer_contract.yaml",
  "source": "examples/customers_bad.csv",
  "status": "FAIL",
  "counts": {"FAIL": 3, "WARN": 1, "INFO": 0},
  "issues": [
    {"severity":"FAIL","check":"column.missing","column":"email","message":"Required column 'email' is missing"}
  ],
  "corrections": [
    {"action":"rename","target":"column","suggestion":"rename 'mail' -> 'email' or update contract"}
  ]
}
```

Agent payloads (included by `enterprise.runtime.EvaluationResult.as_dict()`)

- `analysis` (dict): derived explanations and lists of detected problems/impacts/correctionPlan.
- `recommendations` (list[str]): short actionable steps.
- `generatedCode` (list): snippets with `language` and source code for remediation.
- `llmExplanation` (dict): fields `status`, `statusSource`, `explanation`, `businessImpact`, `proposedCorrection`, `supplierMessage`, `generatedBy`.

Reference: see source code in `contract_agent/core/models.py` for the authoritative implementation.
