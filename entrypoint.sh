#!/bin/sh

echo "Start Testing"
echo "Requirements path : $1"
echo "DAGs directory : $2"
echo "Variable path : $3"

pip install -r $1

airflow initdb > /dev/null

airflow variables --import $3

pytest /app/dag_validation.py -s -q >> result.log
python /app/alert.py --log_filename=result.log --repo_token=$4
