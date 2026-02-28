# -*- coding: utf-8 -*-
"""
Shared utilities for airflow-dag-action.
@author: jayaharyonomanik
"""

import os
import json

RESULTS_FILE = "validation_results.json"
WORKSPACE = os.getenv("GITHUB_WORKSPACE", "/github/workspace")


def read_file(path):
    """Read file contents, or return empty string if missing."""
    if not os.path.isfile(path):
        return ""
    with open(path, encoding="utf-8") as f:
        return f.read()


def load_json(path):
    """Load JSON from file. Returns None if file is missing."""
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def relativize_path(filepath, workspace=None):
    """Return path relative to workspace root."""
    base = workspace if workspace is not None else WORKSPACE
    if filepath.startswith(base):
        return filepath[len(base) :].lstrip("/")
    return filepath
