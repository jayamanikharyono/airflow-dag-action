from airflow import DAG
from airflow.operators.empty import EmptyOperator
from datetime import datetime

with DAG(
    "shared_dag_id",
    start_date=datetime(2024, 1, 1),
    schedule=None,
    default_args={"owner": "team-b"},
    description="Second DAG using same ID — triggers duplicates error",
) as dag:
    EmptyOperator(task_id="task_from_b")
