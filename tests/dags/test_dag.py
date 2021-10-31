from airflow import DAG
from airflow.models import Variable
from airflow.utils.dates import days_ago
from airflow.operators.python_operator import PythonOperator

import numpy as np
import pandas as pd
from datetime import timedelta
import tableauserverclient as TSC

DAG_ID = "test_dag"

default_args = {
    'owner' : 'DE',
    'depends_on_past' : False,
    'start_date' : days_ago(0),
    'email' : ['example@123.com'],
    'email_on_failure' : False,
    'email_on_retry' : False,
    'retries' : 0,
    'retry_delay' : timedelta(minutes=5)
}


dag = DAG(
    DAG_ID,
    description = 'sample dag to test dag',
    default_args = default_args,
    access_control = {
        'DE' : {'can_dag_read', 'can_dag_edit'},
        'BI' : {'can_dag_read'}
    },
    schedule_interval = timedelta(days = 1)
)


def test_import_module():
    import prettyprint
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


access_var >> import_module
