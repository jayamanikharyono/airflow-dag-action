# -*- coding: utf-8 -*-
"""
@author: jayaharyonomanik
"""

from airflow import DAG
from airflow.operators.empty import EmptyOperator

from datetime import datetime

with DAG(
    "shared_dag_id",
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,
    default_args={"owner": "team-a"},
    description="First DAG using a shared ID — triggers duplicates error",
) as dag:
    EmptyOperator(task_id="task_from_a")
