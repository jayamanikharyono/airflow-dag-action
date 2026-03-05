# -*- coding: utf-8 -*-

import json
import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from util import read_file, load_json, relativize_path


class TestReadFile:
    def test_existing_file(self, tmp_path):
        f = tmp_path / "hello.txt"
        f.write_text("hello world", encoding="utf-8")
        assert read_file(str(f)) == "hello world"

    def test_missing_file(self):
        assert read_file("/nonexistent/path/file.txt") == ""

    def test_empty_file(self, tmp_path):
        f = tmp_path / "empty.txt"
        f.write_text("", encoding="utf-8")
        assert read_file(str(f)) == ""


class TestLoadJson:
    def test_valid_json(self, tmp_path):
        f = tmp_path / "data.json"
        f.write_text('{"key": "value"}', encoding="utf-8")
        result = load_json(str(f))
        assert result == {"key": "value"}

    def test_missing_file(self):
        assert load_json("/nonexistent/path/file.json") is None

    def test_invalid_json(self, tmp_path):
        f = tmp_path / "bad.json"
        f.write_text("not json at all", encoding="utf-8")
        with pytest.raises(json.JSONDecodeError):
            load_json(str(f))


class TestRelativizePath:
    def test_path_under_workspace(self):
        result = relativize_path("/github/workspace/dags/my_dag.py", "/github/workspace")
        assert result == "dags/my_dag.py"

    def test_path_outside_workspace(self):
        result = relativize_path("/other/path/file.py", "/github/workspace")
        assert result == "/other/path/file.py"

    def test_none_input(self):
        assert relativize_path(None) == ""

    def test_empty_string(self):
        assert relativize_path("") == ""

    def test_exact_workspace_path(self):
        result = relativize_path("/github/workspace", "/github/workspace")
        assert result == ""
