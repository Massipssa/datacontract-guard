# Contract Format

Data contracts are written in YAML.

They define the expected structure, required fields, data types, and quality rules for a dataset.

---

## Minimal Contract

```yaml
dataset: customers
version: 1.0.0
owner: data-platform

columns:
  - name: customer_id
    type: long
    required: true

  - name: email
    type: string
    required: true
```

---

## Full Example

```yaml
dataset: customers
version: 1.0.0
owner: data-platform
criticality: high

columns:
  - name: customer_id
    type: long
    required: true
    unique: true

  - name: email
    type: string
    required: true
    pii: true
    checks:
      - type: regex
        pattern: "^[^@]+@[^@]+\\.[^@]+$"

  - name: birth_date
    type: date
    required: true
    format: "%Y-%m-%d"

  - name: status
    type: string
    required: false
    allowed_values:
      - ACTIVE
      - INACTIVE

  - name: amount
    type: double
    required: true
    min: 0
```

---

## Dataset-Level Fields

| Field | Required | Description |
|---|---:|---|
| `dataset` | yes | Logical dataset name |
| `version` | no | Contract version |
| `owner` | no | Team or owner responsible for the contract |
| `criticality` | no | Business criticality: `low`, `medium`, `high`, `critical` |
| `columns` | yes | List of expected columns |

---

## Column-Level Fields

| Field | Required | Description |
|---|---:|---|
| `name` | yes | Column name |
| `type` | yes | Expected data type |
| `required` | no | Whether the column must exist and contain values |
| `format` | no | Expected date/timestamp format |
| `pii` | no | Whether the field contains personal data |
| `unique` | no | Whether values must be unique |
| `allowed_values` | no | List of accepted values |
| `min` | no | Minimum numeric value |
| `max` | no | Maximum numeric value |
| `checks` | no | Advanced checks |

---

## Supported Types

Recommended normalized types:

```text
string
integer
long
float
double
decimal
boolean
date
timestamp
```

---

## Supported Rules

### Required Field

```yaml
- name: customer_id
  type: long
  required: true
```

### Date Format

```yaml
- name: birth_date
  type: date
  required: true
  format: "%Y-%m-%d"
```

### Regex

```yaml
- name: email
  type: string
  required: true
  checks:
    - type: regex
      pattern: "^[^@]+@[^@]+\\.[^@]+$"
```

### Allowed Values

```yaml
- name: status
  type: string
  allowed_values:
    - ACTIVE
    - INACTIVE
```

### Min / Max

```yaml
- name: amount
  type: double
  min: 0
  max: 100000
```

---

## Breaking Change Examples

| Change | Impact |
|---|---|
| Remove required column | Breaking |
| Rename required column | Breaking unless mapping exists |
| Change `long` to `string` | Potentially breaking |
| Add optional column | Usually compatible |
| Add required column | Breaking for existing producers |
| Change date format | Potentially breaking |
