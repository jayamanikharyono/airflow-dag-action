# -*- coding: utf-8 -*-
"""
@author: jayaharyonomanik
"""

from airflow import DAG
from airflow.operators.empty import EmptyOperator

from datetime import datetime

with DAG(
    "minimal_dag",
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,
    default_args={"owner": "platform"},
    description="Simplest valid Airflow 2 DAG",
) as dag:
    EmptyOperator(task_id="noop")
