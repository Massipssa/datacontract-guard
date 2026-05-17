# Airflow Integration

DataContract Guard can be used inside Airflow DAGs to validate incoming data before ingestion.

---

## Recommended Flow

```text
S3 Sensor / File Sensor
        ↓
Download or reference incoming file
        ↓
Run DataContract Guard
        ↓
If PASS → continue ingestion
If FAIL → stop pipeline and alert
```

---

## BashOperator Example

```python
from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime

with DAG(
    dag_id="data_contract_validation",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
) as dag:

    validate_contract = BashOperator(
        task_id="validate_contract",
        bash_command="""
        python -B -m contract_agent.cli \
          --source-schema /data/incoming/customers.csv \
          --contract /data/contracts/customers_contract.yaml \
          --source-name customers \
          --output json
        """,
    )
```

---

## PythonOperator Example

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime


def validate_contract():
    from contract_agent.agents.orchestrator import AgentOrchestrator

    orchestrator = AgentOrchestrator()
    report = orchestrator.run(
        source_schema_path="/data/incoming/customers.csv",
        contract_path="/data/contracts/customers_contract.yaml",
        source_name="customers",
    )

    if report.status == "FAIL":
        raise ValueError("Data contract validation failed")


with DAG(
    dag_id="data_contract_validation_python",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
) as dag:

    validate = PythonOperator(
        task_id="validate_contract",
        python_callable=validate_contract,
    )
```

---

## Recommended Airflow Behavior

| Validation Result | DAG Behavior |
|---|---|
| `PASS` | Continue ingestion |
| `FAIL` with critical issues | Fail the task |
| `FAIL` with non-critical issues | Optional: continue with warning |

---

## Alerting

When validation fails, send the report to:

- Slack
- Teams
- Email
- Jira
- Data producer team

Recommended message:

```text
Data contract validation failed for dataset customers.
Critical issue: required column email is missing.
Possible rename candidate: mail.
Action required before ingestion can continue.
```
