# CI/CD Integration

DataContract Guard can be used as a CI/CD quality gate.

The goal is to detect breaking schema changes before deployment or ingestion.

---

## Basic CI Command

```bash
python -B -m contract_agent.cli \
  --source-schema examples/source_schema.json \
  --contract examples/customer_contract.yaml \
  --output json
```

If the validation status is `FAIL`, the process exits with code `1`.

---

## GitLab CI Example

```yaml
stages:
  - test

validate_data_contract:
  stage: test
  image: python:3.11
  script:
    - pip install -r requirements.txt
    - python -B -m contract_agent.cli \
        --source-schema examples/source_schema.json \
        --contract examples/customer_contract.yaml \
        --output json
```

---

## GitHub Actions Example

```yaml
name: Data Contract Check

on:
  pull_request:
    branches:
      - main

jobs:
  validate-data-contract:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Validate data contract
        run: |
          python -B -m contract_agent.cli \
            --source-schema examples/source_schema.json \
            --contract examples/customer_contract.yaml \
            --output json
```

---

## Recommended Pull Request Workflow

```text
Developer opens PR
      ↓
CI runs DataContract Guard
      ↓
Schema drift detected?
      ├── No  → PR can continue
      └── Yes → PR blocked with report
```

---

## Recommended Artifacts

Store the validation report as a CI artifact.

Example:

```yaml
validate_data_contract:
  stage: test
  image: python:3.11
  script:
    - pip install -r requirements.txt
    - python -B -m contract_agent.cli \
        --source-schema examples/source_schema.json \
        --contract examples/customer_contract.yaml \
        --output json > validation-report.json
  artifacts:
    when: always
    paths:
      - validation-report.json
```

---

## When to Run the Check

Recommended triggers:

- Pull requests that modify contracts
- Pull requests that modify ingestion code
- Scheduled validation against incoming samples
- Pre-deployment jobs
- Before publishing to a data warehouse or Iceberg table
