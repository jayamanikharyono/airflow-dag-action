# Airflow-Dag-Validation-Action

Validate DAGs, Variables and Dependencies before deploying it to production by creating an isolated Airflow Environment on Docker Container with supplied variables and dependencies

![Main CI/CD Pipeline](https://github.com/jayamanikharyono/airflow-dag-action/workflows/Main%20CI/CD%20Pipeline/badge.svg)

### Examples of usage scenarios

Want to test airflow DAGs on folder tests/dags, requirements file in tests/requirements.txt and airflow variable file tests/var.json

- Provide your dependency files `requirements.txt` to test your python dependencies
- Your `var.json` to test your variables
- And path to your DAGs directory to test import your DAGs with supplied dependencies and variables

Workflows `.github/workflows/main.yml`
```yml
- name: 'Validate DAGs'
  uses: jayamanikharyono/airflow-dag-action@v2.0
  with:
    requirementsFile: tests/requirements.txt
    dagPaths: tests/dags
    varFile: tests/var.json
    pluginPaths: tests/plugins
    loadExample: False
    accessToken: ${{ secrets.GITHUB_TOKEN }}
```
**Result**
![PR comment](images/comments_pr.png)

### Todo
- Output Validation Result to PR comments ✅
- Upgrading to Airflow 2.0+ ✅
- Add Airflow Plugins Validation ✅


#### Contributions
Contributions are very welcome. You can follow this standard [contributions guidelines](https://github.com/firstcontributions/first-contributions) to contribute code.
