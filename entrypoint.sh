#!/bin/sh
echo "Start Testing"
echo "Requirements path : $1"
echo "DAGs directory : $2"
echo "Variable path : $3"

CURR_DIR=$PWD

pip install -r $CURR_DIR/$1

airflow db init
airflow variables import $CURR_DIR/$3

pytest $CURR_DIR/dag_validation.py -s -q >> result.log
python $CURR_DIR/alert.py --log_filename=result.log --repo_token=$CURR_DIR/$4
