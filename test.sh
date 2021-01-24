#!/bin/sh
var PATH = $1
echo $PATH
sed -i 's/{{dags}}/'"$PATH"'/' dag_validation.py
