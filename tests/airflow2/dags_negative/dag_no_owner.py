# -*- coding: utf-8 -*-
"""
@author: jayaharyonomanik
"""

from airflow import DAG
from airflow.operators.empty import EmptyOperator

from datetime import datetime

with DAG(
    "no_owner_dag",
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,
    description="DAG without explicit owner — triggers owner warning",
) as dag:
    EmptyOperator(task_id="orphan_task")
