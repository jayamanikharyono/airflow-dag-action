# Airflow-Dag-Validation-Action

Validate DAGs file, var and dependencies before deployment to Apache Airflow.

![Main CI/CD Pipeline](https://github.com/jayamanikharyono/airflow-dag-action/workflows/Main%20CI/CD%20Pipeline/badge.svg)

### Using Action Inputs
```yml
- name: 'Validate DAGs'
  uses: jayamanikharyono/airflow-dag-action@v0.1
    with:
      requirementsFile: tests/requirements.txt
      dagPaths: tests/dags
      varFile: tests/var.json
```
