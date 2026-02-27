from airflow import DAG
from airflow.providers.standard.operators.empty import EmptyOperator
from datetime import datetime

with DAG(
    "cycle_dag",
    start_date=datetime(2024, 1, 1),
    schedule=None,
    default_args={"owner": "test"},
    description="DAG with circular dependencies — triggers cycle error",
) as dag:
    task_a = EmptyOperator(task_id="task_a")
    task_b = EmptyOperator(task_id="task_b")
    task_c = EmptyOperator(task_id="task_c")
    task_a >> task_b >> task_c >> task_a
