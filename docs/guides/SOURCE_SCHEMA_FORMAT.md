# Source Schema Format

DataContract Guard can validate either a declared source schema or an actual data file.

---

## JSON Source Schema

Example:

```json
{
  "sourceName": "customers",
  "columns": [
    {
      "name": "customer_id",
      "type": "long"
    },
    {
      "name": "email",
      "type": "string"
    },
    {
      "name": "birth_date",
      "type": "date"
    },
    {
      "name": "amount",
      "type": "double"
    }
  ]
}
```

---

## CSV Source

CSV files can be used directly.

Example:

```csv
customer_id,email,birth_date,amount
123,test@gmail.com,1990-01-01,25.5
456,second@gmail.com,1992-02-14,10.0
```

The Schema Agent should infer:

```json
{
  "columns": [
    {"name": "customer_id", "type": "long"},
    {"name": "email", "type": "string"},
    {"name": "birth_date", "type": "date"},
    {"name": "amount", "type": "double"}
  ]
}
```

---

## Bad CSV Example

```csv
customer_id,mail,birth_date,amount
,test@gmail.com,01/01/1990,25.5
,second@gmail.com,1990-01-02,-3
789,third@gmail.com,1990-02-03,-1
```

Possible detected issues:

- `email` missing
- `mail` unexpected
- `mail` may be a rename candidate for `email`
- `birth_date` contains invalid format
- `customer_id` contains empty values
- `amount` contains negative values

---

## Parquet Source

Parquet support requires `pyarrow`.

Recommended installation:

```bash
pip install pyarrow
```

The Schema Agent can read Parquet metadata and infer column names and types without scanning the entire file where possible.

---

## Type Normalization

Source types should be normalized before comparison.

Examples:

| Raw Type | Normalized Type |
|---|---|
| `int` | `integer` |
| `bigint` | `long` |
| `varchar` | `string` |
| `str` | `string` |
| `float64` | `double` |
| `datetime64` | `timestamp` |

---

## Rename Candidate Detection

The Schema Agent or Contract Agent can detect likely renames by comparing missing and unexpected columns.

Example:

```text
Expected: email
Received: mail
```

Possible output:

```json
{
  "type": "POSSIBLE_RENAME",
  "expectedColumn": "email",
  "actualColumn": "mail",
  "confidence": 0.82
}
```
