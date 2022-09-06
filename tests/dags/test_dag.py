from airflow import DAG
from airflow.models import Variable
from airflow.hooks.base import BaseHook
from airflow.operators.python import PythonOperator
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import (
    KubernetesPodOperator,
)

from shared_var import image
import numpy as np
import pandas as pd
from datetime import timedelta

from common.utils import days_ago # from plugins directory


DAG_ID = "test_dag"

default_args = {
    'owner' : 'DE',
    'depends_on_past' : False,
    'start_date' : days_ago(0),
    'email' : ['example@123.com'],
    'email_on_failure' : False,
    'email_on_retry' : False,
    'retries' : 0,
    'retry_delay' : timedelta(minutes=5),
}


dag = DAG(
    DAG_ID,
    description = 'sample dag to test dag',
    default_args = default_args,
    access_control = {
        'DE' : {'can_read', 'can_edit'},
        'BI' : {'can_read'}
    },
    schedule_interval = timedelta(days = 1)
)


def test_import_module():
    import prettyprint
    from shared_var import image
    return True


def test_access_var():
    my_var = Variable.get("hsfjskdfjhk")
    print("my var message : {}".format(my_var))
    return ("Access Var Success!")


access_var = PythonOperator(
                    task_id = 'test_access_var',
                    python_callable = test_access_var,
                    dag = dag
                )


import_module = PythonOperator(
                    task_id = 'test_import_module',
                    python_callable = test_import_module,
                    dag = dag
                )

r_value = '{"foo": "bar"\n, "buzz": 2}'

k8s_image = KubernetesPodOperator(
                namespace="default",
                image=image,
                cmds=["bash", "-cx"],
                arguments=["echo '{}' > /airflow/xcom/return.json".format(r_value)],
                name="test-k8s-xcom-sidecar",
                task_id="task-test",
                labels={"dag": "test-xcom-sidecar"},
                get_logs=True,
                do_xcom_push=True,
                is_delete_operator_pod=True,
                log_events_on_failure=True,
                dag=dag
            )
BaseHook.get_connection("test_conn")

access_var >> import_module >> k8s_image
