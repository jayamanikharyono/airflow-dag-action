#!/bin/sh

echo "Start Testing"
echo "Req path : $1"
echo "DAGs dir : $2"
echo "Var path : $3"

export AIRFLOW_HOME="/github/workspace/$2"
#export AIRFLOW_HOME="/Users/jayaharyono/Documents/github/airflow-dag-action/tests/dags"
export PYTHONPATH="${PYTHONPATH}:${AIRFLOW_HOME}"

echo "Airflow Home : $AIRFLOW_HOME"
echo "Python : $PYTHONPATH"

pip install -r $1

airflow initdb > /dev/null

airflow variables --import $3

pytest dag_validation.py >> result.log
python util.py --filename=result.log --repo_token=$4
