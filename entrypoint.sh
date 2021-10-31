#!/bin/sh

echo "Start Testing"
echo "Requirements path : $1"
echo "DAGs directory : $2"
echo "Variable path : $3"

export AIRFLOW_HOME="/github/workspace/$2"
export PYTHONPATH="${PYTHONPATH}:${AIRFLOW_HOME}"

echo "Airflow Home : $AIRFLOW_HOME"
echo "Python : $PYTHONPATH"

pip install -r $1

airflow initdb > /dev/null

airflow variables --import $3

pytest dag_validation.py >> result.log
python main.py --log_filename=result.log --repo_token=$4
