#!/bin/sh
echo "Start Testing"
echo "Var file : $1"
echo "DAGs dir : $2"

sed -i "s/{{dags}}/$2/" dag_validation.py

airflow initdb > /dev/null

airflow variables --import $1

pytest dag_validation.py
