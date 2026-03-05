# -*- coding: utf-8 -*-

import os
import sys
from unittest.mock import MagicMock

# Mock github module before importing alert (PyGithub may not be installed)
github_mock = MagicMock()
sys.modules["github"] = github_mock
sys.modules["github.GithubException"] = github_mock.GithubException

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from alert import escape_table_cell, _transform_dag, _transform_error, _transform_warning


class TestEscapeTableCell:
    def test_pipes_escaped(self):
        assert escape_table_cell("a|b|c") == "a\\|b\\|c"

    def test_newlines_replaced(self):
        assert escape_table_cell("line1\nline2") == "line1 line2"

    def test_carriage_return_removed(self):
        assert escape_table_cell("line1\rline2") == "line1line2"

    def test_html_tags_escaped(self):
        result = escape_table_cell("<script>alert('xss')</script>")
        assert "&lt;" in result
        assert "&gt;" in result
        assert "<script>" not in result

    def test_truncation(self):
        long_text = "a" * 250
        result = escape_table_cell(long_text, max_len=200)
        assert len(result) == 203  # 200 + "..."
        assert result.endswith("...")

    def test_no_truncation_under_limit(self):
        text = "short text"
        assert escape_table_cell(text) == "short text"

    def test_non_string_input(self):
        assert escape_table_cell(42) == "42"
        assert escape_table_cell(None) == "None"


class TestTransformDag:
    def test_basic(self):
        dag = {
            "dag_id": "my_dag",
            "file": "/workspace/dags/my_dag.py",
            "task_count": 5,
            "owner": "team-a",
            "schedule": "@daily",
        }
        result = _transform_dag(dag)
        assert result["dag_id"] == "my_dag"
        assert result["file_name"] == "my_dag.py"
        assert result["task_count"] == 5
        assert result["owner"] == "team-a"
        assert result["schedule"] == "@daily"

    def test_missing_fields(self):
        dag = {"dag_id": "minimal"}
        result = _transform_dag(dag)
        assert result["file_name"] == ""
        assert result["task_count"] == 0


class TestTransformError:
    def test_basic(self):
        err = {"rule": "import", "file": "/dags/bad.py", "message": "ModuleNotFoundError"}
        result = _transform_error(err)
        assert result["rule"] == "import"
        assert result["file_name"] == "bad.py"

    def test_missing_rule(self):
        err = {"file": "/dags/bad.py", "message": "oops"}
        result = _transform_error(err)
        assert result["rule"] == "unknown"


class TestTransformWarning:
    def test_basic(self):
        warn = {"rule": "owner", "file": "/dags/test.py", "message": "no owner"}
        result = _transform_warning(warn)
        assert result["rule"] == "owner"
        assert result["file_name"] == "test.py"
