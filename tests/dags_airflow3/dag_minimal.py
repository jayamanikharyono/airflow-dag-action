from airflow import DAG
from airflow.providers.standard.operators.empty import EmptyOperator
from datetime import datetime

with DAG(
    "minimal_dag",
    start_date=datetime(2024, 1, 1),
    schedule=None,
    default_args={"owner": "platform"},
    description="Simplest valid Airflow 3 DAG",
) as dag:
    EmptyOperator(task_id="noop")
