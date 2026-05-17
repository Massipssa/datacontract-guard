# Examples

This document contains practical examples for DataContract Guard.

---

## Example 1: Valid Dataset

### CSV

```csv
customer_id,email,birth_date,amount
123,test@gmail.com,1990-01-01,25.5
456,second@gmail.com,1992-02-14,10.0
```

### Contract

```yaml
dataset: customers
version: 1.0.0

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

### Expected Result

```text
Status: PASS
```

---

## Example 2: Missing Column and Possible Rename

### CSV

```csv
customer_id,mail,birth_date,amount
123,test@gmail.com,1990-01-01,25.5
456,second@gmail.com,1992-02-14,10.0
```

### Expected Result

```text
Status: FAIL

Issues:
- Missing required column: email
- Unexpected column: mail
- Possible rename: email → mail
```

### Suggested Fix

```python
df = df.withColumnRenamed("mail", "email")
```

---

## Example 3: Invalid Date Format

### CSV

```csv
customer_id,email,birth_date,amount
123,test@gmail.com,01/01/1990,25.5
```

### Contract

```yaml
- name: birth_date
  type: date
  required: true
  format: "%Y-%m-%d"
```

### Expected Result

```text
Status: FAIL

Issue:
- birth_date does not match expected format %Y-%m-%d
```

### Suggested Fix

```python
from pyspark.sql.functions import col, to_date

df = df.withColumn("birth_date", to_date(col("birth_date"), "dd/MM/yyyy"))
```

---

## Example 4: Negative Amount

### CSV

```csv
customer_id,email,birth_date,amount
123,test@gmail.com,1990-01-01,-10
```

### Contract

```yaml
- name: amount
  type: double
  required: true
  min: 0
```

### Expected Result

```text
Status: FAIL

Issue:
- amount contains values below 0
```

### Suggested Fix

```python
valid_df = df.filter(col("amount") >= 0)
invalid_df = df.filter(col("amount") < 0)
```

---

## Example 5: Allowed Values

### CSV

```csv
customer_id,status
123,ACTIVE
456,DELETED
```

### Contract

```yaml
- name: status
  type: string
  allowed_values:
    - ACTIVE
    - INACTIVE
```

### Expected Result

```text
Status: FAIL

Issue:
- status contains unsupported value DELETED
```
