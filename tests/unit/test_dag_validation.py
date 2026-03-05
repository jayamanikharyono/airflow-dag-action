# -*- coding: utf-8 -*-

import os
import sys
from io import StringIO
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from dag_validation import _escape_annotation, emit_annotations, ALL_RULES, IMPORT_ERROR_PATTERNS


class TestEscapeAnnotation:
    def test_newlines(self):
        assert _escape_annotation("line1\nline2") == "line1%0Aline2"

    def test_carriage_return(self):
        assert _escape_annotation("line1\rline2") == "line1%0Dline2"

    def test_percent_sign(self):
        assert _escape_annotation("100% done") == "100%25 done"

    def test_combined(self):
        result = _escape_annotation("50%\nok\r")
        assert result == "50%25%0Aok%0D"


class TestEmitAnnotations:
    def test_emits_errors(self, capsys):
        results = {
            "errors": [{"rule": "import", "file": "dags/bad.py", "message": "ModuleNotFoundError"}],
            "warnings": [],
        }
        emit_annotations(results)
        captured = capsys.readouterr()
        assert "::error file=dags/bad.py" in captured.out
        assert "DAG Validation (import)" in captured.out

    def test_emits_warnings(self, capsys):
        results = {
            "errors": [],
            "warnings": [{"rule": "owner", "file": "dags/t.py", "message": "no owner"}],
        }
        emit_annotations(results)
        captured = capsys.readouterr()
        assert "::warning file=dags/t.py" in captured.out

    def test_empty_results(self, capsys):
        results = {"errors": [], "warnings": []}
        emit_annotations(results)
        captured = capsys.readouterr()
        assert captured.out == ""


class TestAllRules:
    def test_contains_core_rules(self):
        for rule in ["import", "cycle", "duplicates", "task_count", "owner", "empty_dag"]:
            assert rule in ALL_RULES

    def test_contains_extended_rules(self):
        for rule in ["schedule", "connection", "config"]:
            assert rule in ALL_RULES


class TestImportErrorPatterns:
    def test_cycle_mapping(self):
        assert IMPORT_ERROR_PATTERNS["AirflowDagCycleException"] == "cycle"

    def test_module_not_found_mapping(self):
        assert IMPORT_ERROR_PATTERNS["ModuleNotFoundError"] == "import"

    def test_connection_mapping(self):
        assert IMPORT_ERROR_PATTERNS["AirflowNotFoundException"] == "connection"
