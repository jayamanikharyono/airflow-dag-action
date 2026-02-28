# -*- coding: utf-8 -*-
"""
@author: jayaharyonomanik
"""

import sys

from util import RESULTS_FILE, load_json

SARIF_SCHEMA = (
    "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/"
    "main/sarif-2.1/schema/sarif-schema-2.1.0.json"
)

RULE_DESCRIPTIONS = {
    "import": "DAG file failed to import due to syntax errors or missing dependencies",
    "cycle": "DAG contains circular task dependencies",
    "duplicates": "Multiple DAGs share the same dag_id",
    "task_count": "DAG exceeds the configured task count threshold",
    "owner": "DAG has no meaningful owner configured",
    "empty_dag": "DAG has no tasks defined",
    "config": "Configuration error in the validation setup",
}


def generate_sarif(results):
    rules_seen = {}
    sarif_results = []

    all_items = [
        (item, "error") for item in results.get("errors", [])
    ] + [
        (item, "warning") for item in results.get("warnings", [])
    ]

    for item, level in all_items:
        rule_id = f"dag-validation/{item['rule']}"
        if rule_id not in rules_seen:
            rules_seen[rule_id] = {
                "id": rule_id,
                "shortDescription": {
                    "text": RULE_DESCRIPTIONS.get(
                        item["rule"], f"DAG validation: {item['rule']}"
                    )
                },
                "defaultConfiguration": {"level": level},
            }

        sarif_results.append({
            "ruleId": rule_id,
            "level": level,
            "message": {"text": item["message"]},
            "locations": [{
                "physicalLocation": {
                    "artifactLocation": {
                        "uri": item["file"],
                        "uriBaseId": "%SRCROOT%",
                    }
                }
            }],
        })

    return {
        "$schema": SARIF_SCHEMA,
        "version": "2.1.0",
        "runs": [{
            "tool": {
                "driver": {
                    "name": "airflow-dag-validation",
                    "informationUri": (
                        "https://github.com/jayamanikharyono/airflow-dag-action"
                    ),
                    "rules": list(rules_seen.values()),
                }
            },
            "results": sarif_results,
        }],
    }


def main():
    sarif_file = "validation_results.sarif"
    results = load_json(RESULTS_FILE)

    if results is None:
        print(f"Results file not found: {RESULTS_FILE}")
        sys.exit(1)

    sarif = generate_sarif(results)

    with open(sarif_file, "w", encoding="utf-8") as f:
        json.dump(sarif, f, indent=2)

    total = len(sarif["runs"][0]["results"])
    print(f"SARIF output written to {sarif_file} ({total} results)")


if __name__ == "__main__":
    main()
