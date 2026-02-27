"""
Sample custom validation tests for the customTests input (P10).

These run via pytest alongside the built-in DAG validation.
Results appear in the PR comment under "Custom Test Results".
"""

import os
from airflow.models import DagBag


DAG_DIR = os.getenv("INPUT_DAGPATHS", "dags").split(",")[0].strip()


def _load_dagbag():
    return DagBag(dag_folder=DAG_DIR, include_examples=False)


def test_dag_ids_are_snake_case():
    """All DAG IDs should be lowercase snake_case."""
    dagbag = _load_dagbag()
    for dag_id in dagbag.dags:
        assert dag_id == dag_id.lower(), f"DAG '{dag_id}' must be lowercase"
        assert " " not in dag_id, f"DAG '{dag_id}' must not contain spaces"


def test_no_hardcoded_connection_strings():
    """DAG files should not contain hardcoded database URIs."""
    forbidden = ["postgresql://", "mysql://", "mongodb://", "redis://"]
    for root, _, files in os.walk(DAG_DIR):
        for fname in files:
            if not fname.endswith(".py") or fname.startswith("__"):
                continue
            filepath = os.path.join(root, fname)
            with open(filepath) as f:
                content = f.read()
            for pattern in forbidden:
                assert pattern not in content, (
                    f"{fname} contains hardcoded connection string '{pattern}'"
                )


def test_all_dags_have_description():
    """All DAGs should have a non-empty description."""
    dagbag = _load_dagbag()
    for dag_id, dag in dagbag.dags.items():
        assert dag.description, f"DAG '{dag_id}' is missing a description"
