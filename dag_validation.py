# -*- coding: utf-8 -*-
"""
@author: jayaharyonomanik
"""

import os
import sys
import json
import time
from collections import deque

WORKSPACE = os.getenv("GITHUB_WORKSPACE", "/github/workspace")
ALL_RULES = ["import", "cycle", "duplicates", "task_count", "owner", "empty_dag"]

IMPORT_ERROR_PATTERNS = {
    "AirflowDagCycleException": "cycle",
    "AirflowDagDuplicatedIdException": "duplicates",
}


def relativize_path(filepath):
    if filepath.startswith(WORKSPACE):
        return filepath[len(WORKSPACE):].lstrip("/")
    return filepath


def has_cycle(dag):
    """Check for cycles using Kahn's topological sort algorithm."""
    graph = {task.task_id: set() for task in dag.tasks}
    in_degree = {task.task_id: 0 for task in dag.tasks}

    for task in dag.tasks:
        for downstream in task.downstream_list:
            graph[task.task_id].add(downstream.task_id)
            in_degree[downstream.task_id] += 1

    queue = deque(tid for tid, d in in_degree.items() if d == 0)
    visited = 0

    while queue:
        node = queue.popleft()
        visited += 1
        for neighbor in graph[node]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    return visited != len(graph)


def validate_dags(dag_dirs, rules, max_task_count=None):
    from airflow.models import DagBag

    results = {
        "status": "pass",
        "dag_dirs": dag_dirs,
        "rules_applied": rules,
        "dags": [],
        "errors": [],
        "warnings": [],
        "summary": {},
    }

    all_dag_ids = {}

    for dag_dir in dag_dirs:
        if not os.path.isdir(dag_dir):
            results["errors"].append({
                "rule": "config",
                "file": dag_dir,
                "message": f"DAG directory not found: {dag_dir}",
            })
            results["status"] = "fail"
            continue

        start_time = time.time()
        dagbag = DagBag(dag_folder=dag_dir, include_examples=False)
        load_duration = time.time() - start_time

        for filepath, error in dagbag.import_errors.items():
            error_str = str(error).strip()
            rule = "import"
            for exception_name, mapped_rule in IMPORT_ERROR_PATTERNS.items():
                if exception_name in error_str and mapped_rule in rules:
                    rule = mapped_rule
                    break
            if rule == "import" and "import" not in rules:
                continue
            results["errors"].append({
                "rule": rule,
                "file": relativize_path(filepath),
                "message": error_str,
            })
            results["status"] = "fail"

        for dag_id, dag in dagbag.dags.items():
            owner = ""
            try:
                owner = dag.default_args.get("owner", "")
            except Exception:
                pass

            schedule = ""
            try:
                if hasattr(dag, "schedule_interval"):
                    schedule = str(dag.schedule_interval)
                elif hasattr(dag, "timetable"):
                    schedule = str(dag.timetable)
            except Exception:
                pass

            dag_info = {
                "dag_id": dag_id,
                "file": relativize_path(dag.fileloc),
                "task_count": len(dag.tasks),
                "tasks": [t.task_id for t in dag.tasks],
                "owner": owner,
                "schedule": schedule,
                "load_duration_s": round(load_duration, 2),
            }
            results["dags"].append(dag_info)

            if dag_id not in all_dag_ids:
                all_dag_ids[dag_id] = []
            all_dag_ids[dag_id].append(relativize_path(dag.fileloc))

            if "cycle" in rules and len(dag.tasks) > 0:
                if has_cycle(dag):
                    results["errors"].append({
                        "rule": "cycle",
                        "file": relativize_path(dag.fileloc),
                        "message": f"DAG '{dag_id}' contains a cycle in task dependencies",
                    })
                    results["status"] = "fail"

            if "empty_dag" in rules and len(dag.tasks) == 0:
                results["warnings"].append({
                    "rule": "empty_dag",
                    "file": relativize_path(dag.fileloc),
                    "message": f"DAG '{dag_id}' has no tasks",
                })

            if "task_count" in rules and max_task_count is not None:
                if len(dag.tasks) > max_task_count:
                    results["warnings"].append({
                        "rule": "task_count",
                        "file": relativize_path(dag.fileloc),
                        "message": (
                            f"DAG '{dag_id}' has {len(dag.tasks)} tasks "
                            f"(threshold: {max_task_count})"
                        ),
                    })

            if "owner" in rules:
                if not owner or owner == "airflow":
                    results["warnings"].append({
                        "rule": "owner",
                        "file": relativize_path(dag.fileloc),
                        "message": f"DAG '{dag_id}' has no meaningful owner (got: '{owner}')",
                    })

    if "duplicates" in rules:
        for dag_id, files in all_dag_ids.items():
            if len(files) > 1:
                results["errors"].append({
                    "rule": "duplicates",
                    "file": files[0],
                    "message": f"Duplicate DAG ID '{dag_id}' found in: {', '.join(files)}",
                })
                results["status"] = "fail"

    results["summary"] = {
        "total_dags": len(results["dags"]),
        "total_errors": len(results["errors"]),
        "total_warnings": len(results["warnings"]),
        "dag_dirs_checked": len(dag_dirs),
    }

    return results


def emit_annotations(results):
    """Emit GitHub Actions workflow commands for file-level annotations."""
    for error in results["errors"]:
        filepath = error.get("file", "")
        message = error.get("message", "").replace("\n", "%0A").replace("\r", "")
        rule = error.get("rule", "")
        print(f"::error file={filepath},title=DAG Validation ({rule})::{message}")

    for warning in results["warnings"]:
        filepath = warning.get("file", "")
        message = warning.get("message", "").replace("\n", "%0A").replace("\r", "")
        rule = warning.get("rule", "")
        print(f"::warning file={filepath},title=DAG Validation ({rule})::{message}")


def main():
    dag_paths = os.getenv("INPUT_DAGPATHS", "dags")
    dag_dirs = [d.strip() for d in dag_paths.split(",")]

    rules_input = os.getenv("INPUT_VALIDATIONRULES", "all")
    if rules_input == "all":
        rules = list(ALL_RULES)
    else:
        rules = [r.strip() for r in rules_input.split(",")]

    max_task_count = None
    max_task_count_str = os.getenv("INPUT_MAXTASKCOUNT", "")
    if max_task_count_str:
        try:
            max_task_count = int(max_task_count_str)
        except ValueError:
            print(f"::warning::Invalid maxTaskCount value: {max_task_count_str}")

    results = validate_dags(dag_dirs, rules, max_task_count)

    with open("validation_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)

    emit_annotations(results)

    status_label = "PASSED" if results["status"] == "pass" else "FAILED"
    print(f"\n{'=' * 50}")
    print(f" Validation {status_label}")
    print(f"{'=' * 50}")
    print(f"DAGs found    : {results['summary']['total_dags']}")
    print(f"Errors        : {results['summary']['total_errors']}")
    print(f"Warnings      : {results['summary']['total_warnings']}")
    print(f"Rules applied : {', '.join(results['rules_applied'])}")

    if results["dags"]:
        print("\nDAGs:")
        for dag in results["dags"]:
            print(f"  - {dag['dag_id']} ({dag['task_count']} tasks) [{dag['file']}]")

    if results["errors"]:
        print("\nErrors:")
        for err in results["errors"]:
            print(f"  [{err['rule']}] {err['file']}: {err['message'][:200]}")

    if results["warnings"]:
        print("\nWarnings:")
        for warn in results["warnings"]:
            print(f"  [{warn['rule']}] {warn['file']}: {warn['message']}")

    sys.exit(0 if results["status"] == "pass" else 1)


if __name__ == "__main__":
    main()
