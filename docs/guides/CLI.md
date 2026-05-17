# CLI Usage

DataContract Guard can be used from the command line to validate source schemas or data files against YAML data contracts.

---

## Basic Validation

```bash
python -B -m contract_agent.cli \
  --source-schema examples/source_schema.json \
  --contract examples/customer_contract.yaml
```

---

## JSON Output

```bash
python -B -m contract_agent.cli \
  --source-schema examples/source_schema.json \
  --contract examples/customer_contract.yaml \
  --output json
```

---

## Markdown Output

```bash
python -B -m contract_agent.cli \
  --source-schema examples/source_schema.json \
  --contract examples/customer_contract.yaml \
  --output markdown
```

---

## Validate a CSV File

```bash
python -B -m contract_agent.cli \
  --source-schema examples/customers_bad.csv \
  --contract examples/customers_contract.yaml \
  --source-name customers
```

---

## Exit Codes

| Exit Code | Meaning |
|---:|---|
| `0` | Validation passed |
| `1` | Validation failed |
| `2` | Invalid CLI usage or runtime error |

This behavior makes the CLI useful as a CI/CD gate.

---

## Recommended CLI Options

| Option | Description |
|---|---|
| `--source-schema` | Path to JSON schema, CSV file, or supported data file |
| `--contract` | Path to YAML contract |
| `--source-name` | Logical dataset name |
| `--output` | Output format: `json` or `markdown` |
| `--validate-data` | Enable data quality validation when data is available |
| `--fail-on-warning` | Treat warnings as failures |

---

## Example CI Command

```bash
python -B -m contract_agent.cli \
  --source-schema examples/source_schema.json \
  --contract examples/customer_contract.yaml \
  --output json
```

If the validation status is `FAIL`, the command exits with code `1` and the pipeline should fail.
