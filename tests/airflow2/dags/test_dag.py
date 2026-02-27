from airflow import DAG
from airflow.models import Variable
from airflow.hooks.base import BaseHook
from airflow.operators.python import PythonOperator
try:
    from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator
except ImportError:
    from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import KubernetesPodOperator

from shared_var import image
import numpy as np
import pandas as pd
from datetime import timedelta

from common.utils import days_ago


default_args = {
    'owner': 'DE',
    'depends_on_past': False,
    'start_date': days_ago(0),
    'email': ['example@123.com'],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 0,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    "test_dag",
    description='Airflow 2 DAG with variables, connections, plugins and K8s operator',
    default_args=default_args,
    schedule_interval=timedelta(days=1),
)


def test_import_module():
    import prettyprint
    from shared_var import image
    return True


def test_access_var():
    my_var = Variable.get("hsfjskdfjhk")
    return "Access Var Success!"


access_var = PythonOperator(
    task_id='test_access_var', python_callable=test_access_var, dag=dag,
)
import_module = PythonOperator(
    task_id='test_import_module', python_callable=test_import_module, dag=dag,
)
k8s_image = KubernetesPodOperator(
    namespace="default", image=image, cmds=["bash", "-cx"],
    arguments=["echo done"], name="test-k8s", task_id="task-test",
    get_logs=True, do_xcom_push=True, is_delete_operator_pod=True,
    log_events_on_failure=True, dag=dag,
)

BaseHook.get_connection("test_conn")
access_var >> import_module >> k8s_image
