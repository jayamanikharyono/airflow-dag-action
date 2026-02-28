# Airflow-Dag-Validation-Action

Validate DAGs, Variables and Dependencies before deploying to production by creating an isolated Airflow Environment on Docker Container with supplied variables and dependencies.

Supports **Airflow 2.x** and **Airflow 3.x**.

![Test with Airflow 2](https://github.com/jayamanikharyono/airflow-dag-action/workflows/Test%20with%20Airflow%202/badge.svg)
![Test with Airflow 3](https://github.com/jayamanikharyono/airflow-dag-action/workflows/Test%20with%20Airflow%203/badge.svg)

## Examples of usage scenarios

Want to test Airflow DAGs in `tests/dags` with plugins in `tests/plugins`, requirements in `tests/requirements.txt`, variables in `tests/var.json`, and connections in `tests/conns.json`?

- Provide your **dependency files** (`requirements.txt`) to test your Python dependencies
- Your **`var.json`** to test your variables
- Your **`conns.json`** to test your connections
- **Path to your DAGs directory** to import and validate DAGs with supplied dependencies and variables
- **Path to your DAG plugins directory** to test DAGs using plugins
- **Boolean flag** for whether to load example DAGs or not

## Usage

### Airflow 2

```yml
- name: 'Validate DAGs'
  uses: jayamanikharyono/airflow-dag-action@v3
  with:
    dagPaths: dags
    pluginPaths: plugins
    requirementsFile: requirements.txt
    varFile: var.json
    connFile: conns.json
    accessToken: ${{ secrets.GITHUB_TOKEN }}
    airflowVersion: "2.10.4"
    airflowExtras: "async,postgres,cncf.kubernetes"
```

### Airflow 3

```yml
- name: 'Validate DAGs'
  uses: jayamanikharyono/airflow-dag-action@v3
  with:
    dagPaths: dags
    pluginPaths: plugins
    requirementsFile: requirements.txt
    varFile: var.json
    connFile: conns.json
    accessToken: ${{ secrets.GITHUB_TOKEN }}
    airflowVersion: "3.1.7"
    airflowExtras: "cncf.kubernetes"
    validationRules: "all"
    enableSarif: "true"
```

**Result**

**Airflow 2 Sample Comments**
![Airflow 2 PR comment](images/airflow2_comments_pr.png)
**Airflow 3 Sample Comments**
![Airflow 3 PR comment](images/airflow3_comments_pr.png)

## Inputs

| Input | Required | Default | Description |
|-------|----------|---------|-------------|
| `dagPaths` | No | `"dags"` | DAG directories to validate (comma-separated for multiple) |
| `pluginPaths` | No | `"plugins"` | Plugin directory |
| `requirementsFile` | No | `"requirements.txt"` | Path to pip requirements file |
| `varFile` | No | `""` | Path to Airflow variables JSON file |
| `connFile` | No | `""` | Path to Airflow connections JSON file |
| `loadExamples` | No | `"False"` | Whether to load example DAGs |
| `accessToken` | **Yes** | — | GitHub token for PR comments |
| `airflowVersion` | No | `"2.10.4"` | Apache Airflow version |
| `pythonVersion` | No | `"3.11"` | Python version for constraint resolution |
| `airflowExtras` | No | `"async,postgres"` | Comma-separated Airflow extras |
| `additionalPips` | No | `""` | Space-separated additional pip packages |
| `validationRules` | No | `"all"` | Rules to run: `import,cycle,duplicates,task_count,owner,empty_dag` or `"all"` |
| `maxTaskCount` | No | `""` | Max tasks per DAG before warning (empty = no limit) |
| `customTests` | No | `""` | Path to custom pytest validation file |
| `failOnError` | No | `"true"` | Set to `"false"` for warning-only mode |
| `enableSarif` | No | `"false"` | Generate SARIF output for code scanning |

## Outputs

| Output | Description |
|--------|-------------|
| `validator-result` | `pass` or `fail` |
| `sarif-file` | Path to SARIF file (when `enableSarif` is `"true"`) |

## Validation Rules

| Rule | Type | Description |
|------|------|-------------|
| `import` | Error | DAG fails to import (syntax errors, missing deps) |
| `cycle` | Error | Circular task dependencies |
| `duplicates` | Error | Multiple DAGs with the same `dag_id` |
| `task_count` | Warning | DAG exceeds `maxTaskCount` threshold |
| `owner` | Warning | Missing or default owner |
| `empty_dag` | Warning | DAG has zero tasks |

## Features

- Structured Markdown PR comments with DAG tables, errors, and warnings
- File-level GitHub Actions annotations on PR diffs
- SARIF output for GitHub code scanning integration
- Multiple DAG directory validation
- Custom pytest validation scripts
- Warning-only mode (`failOnError: "false"`)
- Pip dependency caching support
- Pre-built Docker images via GHCR

## SARIF Integration

```yml
- name: 'Validate DAGs'
  id: validate
  uses: jayamanikharyono/airflow-dag-action@v3
  with:
    dagPaths: dags
    accessToken: ${{ secrets.GITHUB_TOKEN }}
    enableSarif: "true"

- name: Upload SARIF
  if: always() && steps.validate.outputs.sarif-file != ''
  uses: github/codeql-action/upload-sarif@v3
  with:
    sarif_file: validation_results.sarif
    category: airflow-dag-validation
```

## Todo

- [x] Output Validation Result to PR comments
- [x] Upgrading to Airflow 2.0+
- [x] Add Airflow Plugins Validation
- [x] Add Airflow Connections Validation
- [ ] Output Detailed Validation Result for Plugins and Connections
- [x] Possibility to have default and specified Python Version by user/developer via Arguments/Env Variable

## Contributions

Contributions are very welcome. You can follow this standard [contributions guidelines](https://github.com/firstcontributions/first-contributions) to contribute code.
