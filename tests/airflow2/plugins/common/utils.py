# -*- coding: utf-8 -*-
"""
@author: jayaharyonomanik
"""

import airflow.utils.python_virtualenv
from airflow.plugins_manager import AirflowPlugin

import pendulum
import datetime as dt
from datetime import timedelta


def days_ago(n, hour=0, minute=0, second=0, microsecond=0, timezone="utc"):
    """Choose a number of days ago based on midnight local time, instead of midnight UTC"""
    try:
        tz = pendulum.timezone(timezone)
    except AttributeError:
        tz = pendulum.tz.timezone(timezone)
    today = dt.datetime.now(tz=tz).replace(
        hour=hour, minute=minute, second=second, microsecond=microsecond
    )
    return today - timedelta(days=n)

# Workaround for https://github.com/apache/airflow/issues/17720
airflow.utils.python_virtualenv._generate_virtualenv_cmd = days_ago


class VirtualPythonPlugin(AirflowPlugin):
    name = 'days_ago_plugin'
