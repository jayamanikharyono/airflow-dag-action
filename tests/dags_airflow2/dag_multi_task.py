from airflow import DAG
from airflow.operators.empty import EmptyOperator
from datetime import datetime, timedelta

default_args = {
    "owner": "data-engineering",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "email": ["data-eng@example.com"],
    "email_on_failure": True,
}

with DAG(
    "etl_pipeline",
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule_interval="@daily",
    catchup=False,
    description="Airflow 2 multi-stage ETL pipeline",
) as dag:

    start = EmptyOperator(task_id="start")
    extract_users = EmptyOperator(task_id="extract_users")
    extract_orders = EmptyOperator(task_id="extract_orders")
    extract_products = EmptyOperator(task_id="extract_products")
    transform = EmptyOperator(task_id="transform")
    load = EmptyOperator(task_id="load")
    notify = EmptyOperator(task_id="notify")

    start >> [extract_users, extract_orders, extract_products] >> transform >> load >> notify
