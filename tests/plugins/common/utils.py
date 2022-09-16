from airflow.plugins_manager import AirflowPlugin
import airflow.utils.python_virtualenv

import datetime as dt
from datetime import timedelta

import pendulum

# Thanks https://github.com/apache/airflow/issues/17720


def days_ago(n, hour=0, minute=0, second=0, microsecond=0, timezone="utc"):
    """Choose a number of days ago based on midnight local time, instead of midnight UTC"""
    tz = pendulum.tz.timezone(timezone)
    today = dt.datetime.now(tz=tz).replace(
        hour=hour, minute=minute, second=second, microsecond=microsecond
    )
    return today - timedelta(days=n)

airflow.utils.python_virtualenv._generate_virtualenv_cmd=days_ago

class VirtualPythonPlugin(AirflowPlugin):
    name = 'days_ago_plugin'