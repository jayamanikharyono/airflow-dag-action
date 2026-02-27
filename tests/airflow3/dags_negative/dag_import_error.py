from airflow import DAG
from nonexistent_provider.operators import FakeOperator
from datetime import datetime

with DAG("broken_dag", start_date=datetime(2024, 1, 1), schedule=None) as dag:
    FakeOperator(task_id="will_never_work")
