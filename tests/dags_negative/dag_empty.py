from airflow import DAG
from datetime import datetime

dag = DAG(
    "empty_dag",
    start_date=datetime(2024, 1, 1),
    schedule=None,
    default_args={"owner": "test"},
    description="DAG with zero tasks — triggers empty_dag warning",
)
