# Airflow-Dag-Validation-Action

Validate DAGs, Variables and Dependencies before deploying to production by creating an isolated Airflow Environment on Docker Container with supplied variables and dependencies.

Supports **Airflow 2.x** and **Airflow 3.x**.

![Test with Airflow 2](https://github.com/jayamanikharyono/airflow-dag-action/workflows/Test%20with%20Airflow%202/badge.svg)
![Test with Airflow 3](https://github.com/jayamanikharyono/airflow-dag-action/workflows/Test%20with%20Airflow%203/badge.svg)

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

## Contributions

Contributions are very welcome. You can follow this standard [contributions guidelines](https://github.com/firstcontributions/first-contributions) to contribute code.
