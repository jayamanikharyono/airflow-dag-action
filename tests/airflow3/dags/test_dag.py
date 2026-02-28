# -*- coding: utf-8 -*-
"""
@author: jayaharyonomanik
"""

from airflow import DAG
from airflow.models import Variable
from airflow.sdk.bases.hook import BaseHook
from airflow.providers.standard.operators.python import PythonOperator
from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator


import numpy as np
import pandas as pd
from datetime import timedelta

from shared_var import image
from common.utils import days_ago


default_args = {
    'owner': 'DE',
    'depends_on_past': False,
    'start_date': days_ago(0),
    'retries': 0,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    "test_dag",
    description='Airflow 3 DAG with variables, connections, plugins and K8s operator',
    default_args=default_args,
    schedule=timedelta(days=1),
) as dag:

    def test_import_module():
        import prettyprint
        from shared_var import image
        return True

    def test_access_var():
        my_var = Variable.get("hsfjskdfjhk")
        return "Access Var Success!"

    def _check_connection():
        BaseHook.get_connection("test_conn")
        return True


    access_var = PythonOperator(
        task_id='test_access_var', python_callable=test_access_var,
    )

    import_module = PythonOperator(
        task_id='test_import_module', python_callable=test_import_module,
    )

    k8s_image = KubernetesPodOperator(
        namespace="default", image=image, cmds=["bash", "-cx"],
        arguments=["echo done"], name="test-k8s", task_id="task-test",
        get_logs=True, do_xcom_push=True, on_finish_action="delete_pod",
        log_events_on_failure=True,
    )

    check_conn = PythonOperator(
        task_id='check_connection', python_callable=_check_connection
    )

    access_var >> import_module >> check_conn >> k8s_image
