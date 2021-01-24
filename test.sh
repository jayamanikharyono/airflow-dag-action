#!/bin/sh
#awk {sub("{{dags}}","$1")}1 dag_validation.py > temp.txt && mv temp.txt dag_validation.py
#perl -pe 's/{{dags}}/'$1'/' dag_validation.py > temp.txt && mv temp.txt dag_validation.py
jinja2 dag_validation.py -D dags=$1 > temp.txt && mv temp.txt dag_validation.py
