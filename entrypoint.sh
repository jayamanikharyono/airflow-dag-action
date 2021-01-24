#!/bin/sh

echo "Start Testing"
echo "Req path : $1"
echo "Var path : $2"
echo "DAGs dir : $3"

export AIRFLOW_HOME="/github/workspace/$3"
export PYTHONPATH="${PYTHONPATH}:${AIRFLOW_HOME}"

echo "Airflow : $AIRFLOW_HOME"
echo "Python : $PYTHONPATH"

pip install -r $1

sed -i 's/{{dags}}/$3/' dag_validation.py

cat dag_validation.py

airflow initdb > /dev/null

airflow variables --import $2

pytest dag_validation.py
