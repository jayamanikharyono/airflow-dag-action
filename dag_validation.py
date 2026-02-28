# -*- coding: utf-8 -*-
"""
@author: jayaharyonomanik
"""

import os
import sys
import json
import time

from util import RESULTS_FILE, relativize_path

ALL_RULES = [
    "import",
    "cycle",
    "duplicates",
    "task_count",
    "owner",
    "empty_dag",
    "schedule",
    "connection",
    "config",
]

IMPORT_ERROR_PATTERNS = {
    "AirflowDagCycleException": "cycle",
    "AirflowDagDuplicatedIdException": "duplicates",
    "ModuleNotFoundError": "import",
    "AirflowNotFoundException": "connection",
    "AirflowTimetableInvalid": "schedule",
    "ValueError": "config",
}

# Use Airflow's built-in cycle detection when available (AF2); not available in AF3
try:
    from airflow.utils.dag_cycle_tester import check_cycle
    from airflow.exceptions import AirflowDagCycleException

    def has_cycle(dag):
        try:
            check_cycle(dag)
            return False
        except AirflowDagCycleException:
            return True
except ImportError:
    has_cycle = None  # Cycle check not available (e.g. Airflow 3)

_CYCLE_UNAVAILABLE_WARNED = False


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
    load_durations = []

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
        load_durations.append(load_duration)

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
                for attr in ("schedule", "schedule_interval", "timetable"):
                    val = getattr(dag, attr, None)
                    if val is not None:
                        schedule = str(val)
                        if "NullTimetable" in schedule:
                            schedule = "None"
                        break
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
                if has_cycle is None:
                    global _CYCLE_UNAVAILABLE_WARNED
                    if not _CYCLE_UNAVAILABLE_WARNED:
                        print("::warning::Cycle check not available (airflow.utils.dag_cycle_tester)")
                        _CYCLE_UNAVAILABLE_WARNED = True
                elif has_cycle(dag):
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
        "min_load_duration_s": round(min(load_durations), 2) if load_durations else None,
        "max_load_duration_s": round(max(load_durations), 2) if load_durations else None,
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

    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)

    emit_annotations(results)

    status_label = "PASSED" if results["status"] == "pass" else "FAILED"
    print(f"\n{'=' * 50}")
    print(f" Validation {status_label}")
    print(f"{'=' * 50}")
    print(f"DAGs found    : {results['summary']['total_dags']}")
    print(f"Errors        : {results['summary']['total_errors']}")
    print(f"Warnings      : {results['summary']['total_warnings']}")
    summary = results["summary"]
    if summary.get("min_load_duration_s") is not None and summary.get("max_load_duration_s") is not None:
        print(f"Load duration : {summary['min_load_duration_s']}s–{summary['max_load_duration_s']}s (min–max)")
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
