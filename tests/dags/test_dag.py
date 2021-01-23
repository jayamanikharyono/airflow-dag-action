from datetime import timedelta
from airflow.utils.dates import days_ago

from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.models import Variable

import util

DAG_ID = util.get_dag_id(__file__)

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


def test_template():
    print('{{ egg_version }}')
    return ("Test Templating!")


template_task = PythonOperator(
                    task_id = 'template_task',
                    python_callable = test_template,
                    dag = dag
                )


template_task
