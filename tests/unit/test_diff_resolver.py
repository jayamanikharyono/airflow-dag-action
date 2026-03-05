# -*- coding: utf-8 -*-
import json
import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from diff_resolver import (
    _read_event,
    _get_pr_number,
    _get_base_sha,
    filter_dag_paths,
    get_changed_files,
)


class TestReadEvent(unittest.TestCase):
    def test_valid_json(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"number": 42}, f)
            f.flush()
            result = _read_event(f.name)
        self.assertEqual(result, {"number": 42})
        os.unlink(f.name)

    def test_missing_file(self):
        self.assertEqual(_read_event("/nonexistent/path.json"), {})

    def test_empty_path(self):
        self.assertEqual(_read_event(""), {})

    def test_none_path(self):
        self.assertEqual(_read_event(None), {})


class TestGetPrNumber(unittest.TestCase):
    def test_top_level_number(self):
        self.assertEqual(_get_pr_number({"number": 42}), 42)

    def test_nested_pr_number(self):
        event = {"pull_request": {"number": 99}}
        self.assertEqual(_get_pr_number(event), 99)

    def test_zero_number(self):
        self.assertIsNone(_get_pr_number({"number": 0}))

    def test_no_number(self):
        self.assertIsNone(_get_pr_number({"action": "push"}))

    def test_empty_event(self):
        self.assertIsNone(_get_pr_number({}))


class TestGetBaseSha(unittest.TestCase):
    def test_pr_base_sha(self):
        event = {"pull_request": {"base": {"sha": "abc123"}}}
        self.assertEqual(_get_base_sha(event), "abc123")

    def test_push_before(self):
        event = {"before": "def456"}
        self.assertEqual(_get_base_sha(event), "def456")

    def test_pr_base_takes_priority(self):
        event = {
            "before": "push_sha",
            "pull_request": {"base": {"sha": "pr_sha"}},
        }
        self.assertEqual(_get_base_sha(event), "pr_sha")

    def test_all_zeros_sha(self):
        event = {"before": "0" * 40}
        self.assertIsNone(_get_base_sha(event))

    def test_empty_event(self):
        self.assertIsNone(_get_base_sha({}))

    def test_empty_sha(self):
        event = {"pull_request": {"base": {"sha": ""}}, "before": ""}
        self.assertIsNone(_get_base_sha(event))


class TestFilterDagPaths(unittest.TestCase):
    def test_single_dir_match(self):
        result = filter_dag_paths("dags", ["dags/my_dag.py", "README.md"])
        self.assertEqual(result, "dags")

    def test_single_dir_no_match(self):
        result = filter_dag_paths("dags", ["src/app.py", "README.md"])
        self.assertEqual(result, "")

    def test_multiple_dirs_partial_match(self):
        result = filter_dag_paths(
            "dags/etl,dags/ml,dags/analytics",
            ["dags/etl/pipeline.py", "dags/analytics/report.py"],
        )
        self.assertEqual(result, "dags/etl,dags/analytics")

    def test_multiple_dirs_all_match(self):
        result = filter_dag_paths(
            "dags,plugins",
            ["dags/my_dag.py", "plugins/hook.py"],
        )
        self.assertEqual(result, "dags,plugins")

    def test_no_match_returns_empty(self):
        result = filter_dag_paths("dags", ["tests/test_app.py"])
        self.assertEqual(result, "")

    def test_trailing_commas_ignored(self):
        result = filter_dag_paths("dags,,plugins,", ["dags/my_dag.py"])
        self.assertEqual(result, "dags")

    def test_whitespace_trimmed(self):
        result = filter_dag_paths(" dags , plugins ", ["dags/my_dag.py"])
        self.assertEqual(result, "dags")

    def test_no_false_prefix_match(self):
        """'dags' should not match 'dags_negative/file.py' (requires trailing slash)."""
        result = filter_dag_paths("dags", ["dags_negative/bad_dag.py"])
        self.assertEqual(result, "")

    def test_nested_dir(self):
        result = filter_dag_paths("src/dags", ["src/dags/etl.py"])
        self.assertEqual(result, "src/dags")


class TestGetChangedFiles(unittest.TestCase):
    @patch.dict(os.environ, {"GITHUB_EVENT_PATH": ""})
    def test_no_event_path(self):
        self.assertIsNone(get_changed_files())

    @patch.dict(os.environ, {"GITHUB_EVENT_PATH": "/nonexistent.json"})
    def test_missing_event_file(self):
        self.assertIsNone(get_changed_files())


if __name__ == "__main__":
    unittest.main()
