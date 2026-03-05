# -*- coding: utf-8 -*-

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from sarif_output import generate_sarif, _extract_line_number, RULE_DESCRIPTIONS


class TestExtractLineNumber:
    def test_traceback_line(self):
        msg = '  File "/dags/bad.py", line 12, in <module>'
        assert _extract_line_number(msg) == 12

    def test_uppercase_line(self):
        assert _extract_line_number("Error at Line 42") == 42

    def test_no_line_number(self):
        assert _extract_line_number("ModuleNotFoundError: no module named 'foo'") is None

    def test_multiple_line_refs(self):
        msg = 'line 5 then line 10'
        assert _extract_line_number(msg) == 5


class TestRuleDescriptions:
    def test_all_rules_covered(self):
        expected = ["import", "cycle", "duplicates", "task_count", "owner",
                     "empty_dag", "config", "schedule", "connection"]
        for rule in expected:
            assert rule in RULE_DESCRIPTIONS, f"Missing RULE_DESCRIPTION for '{rule}'"


class TestGenerateSarif:
    def test_empty_results(self):
        results = {"errors": [], "warnings": []}
        sarif = generate_sarif(results)
        assert sarif["version"] == "2.1.0"
        assert len(sarif["runs"][0]["results"]) == 0
        assert len(sarif["runs"][0]["tool"]["driver"]["rules"]) == 0

    def test_error_produces_result(self):
        results = {
            "errors": [{"rule": "import", "file": "dags/bad.py", "message": "ModuleNotFoundError"}],
            "warnings": [],
        }
        sarif = generate_sarif(results)
        assert len(sarif["runs"][0]["results"]) == 1
        r = sarif["runs"][0]["results"][0]
        assert r["ruleId"] == "dag-validation/import"
        assert r["level"] == "error"
        assert r["locations"][0]["physicalLocation"]["artifactLocation"]["uri"] == "dags/bad.py"

    def test_warning_produces_result(self):
        results = {
            "errors": [],
            "warnings": [{"rule": "owner", "file": "dags/test.py", "message": "no owner"}],
        }
        sarif = generate_sarif(results)
        assert len(sarif["runs"][0]["results"]) == 1
        assert sarif["runs"][0]["results"][0]["level"] == "warning"

    def test_line_number_in_region(self):
        results = {
            "errors": [{
                "rule": "import",
                "file": "dags/bad.py",
                "message": 'File "/dags/bad.py", line 7, in <module>',
            }],
            "warnings": [],
        }
        sarif = generate_sarif(results)
        region = sarif["runs"][0]["results"][0]["locations"][0]["physicalLocation"].get("region")
        assert region is not None
        assert region["startLine"] == 7

    def test_missing_file_key(self):
        results = {
            "errors": [{"rule": "config", "message": "something broke"}],
            "warnings": [],
        }
        sarif = generate_sarif(results)
        uri = sarif["runs"][0]["results"][0]["locations"][0]["physicalLocation"]["artifactLocation"]["uri"]
        assert uri == ""

    def test_missing_rule_key(self):
        results = {
            "errors": [{"file": "dags/x.py", "message": "oops"}],
            "warnings": [],
        }
        sarif = generate_sarif(results)
        assert sarif["runs"][0]["results"][0]["ruleId"] == "dag-validation/unknown"

    def test_deduplicates_rules(self):
        results = {
            "errors": [
                {"rule": "import", "file": "a.py", "message": "err1"},
                {"rule": "import", "file": "b.py", "message": "err2"},
            ],
            "warnings": [],
        }
        sarif = generate_sarif(results)
        assert len(sarif["runs"][0]["tool"]["driver"]["rules"]) == 1
        assert len(sarif["runs"][0]["results"]) == 2
