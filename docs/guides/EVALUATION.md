# Evaluation

Evaluation ensures DataContract Guard keeps producing expected validation results over time.

---

## Why Evaluation Matters

Data contract validation must be stable.

A change in code should not accidentally change:

- validation status
- issue types
- severity levels
- generated remediation actions
- output format

---

## Run Evaluation

```bash
python -B -m contract_agent.evaluation --eval-file examples/evaluation_cases.json
```

---

## Example Evaluation Case

```json
{
  "name": "missing_email_with_mail_candidate",
  "source": "examples/customers_bad.csv",
  "contract": "examples/customers_contract.yaml",
  "expectedStatus": "FAIL",
  "expectedIssues": [
    "MISSING_COLUMN",
    "POSSIBLE_RENAME"
  ],
  "expectedCorrections": [
    "RENAME_COLUMN"
  ]
}
```

---

## Recommended Checks

Each evaluation case should verify:

- expected status
- expected issue types
- expected severity levels
- expected correction actions
- no unexpected critical issue

---

## Golden Files

For stable reports, store expected outputs as golden files.

```text
examples/golden/
├── customers_bad_report.json
├── customers_valid_report.json
└── invalid_date_report.json
```

Then compare generated reports with golden reports in CI.

---

## CI Integration

```yaml
evaluate_reports:
  stage: test
  image: python:3.11
  script:
    - pip install -r requirements.txt
    - python -B -m contract_agent.evaluation --eval-file examples/evaluation_cases.json
```
