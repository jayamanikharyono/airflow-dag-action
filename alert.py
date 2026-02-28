# -*- coding: utf-8 -*-
"""
@author: jayaharyonomanik
"""

import os
import json
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
from github import Github, Auth
from github.GithubException import GithubException, BadCredentialsException

from util import RESULTS_FILE, read_file, load_json

ENV_INFO_FILE = "env_info.log"
CUSTOM_RESULTS_FILE = "custom_results.log"
TEMPLATE_NAME = "comment.md.j2"


def escape_table_cell(text, max_len=200):
    """Escape and truncate text for use in Markdown table cells."""
    text = str(text).replace("|", "\\|").replace("\n", " ").replace("\r", "")
    text = text.replace("<", "&lt;").replace(">", "&gt;")  # Prevent HTML tag parsing
    return text[:max_len] + "..." if len(text) > max_len else text


def _transform_dag(dag):
    """Convert a DAG result into template-ready dict."""
    return {
        "dag_id": escape_table_cell(dag["dag_id"], 60),
        "file_name": os.path.basename(dag.get("file", "")),
        "task_count": dag.get("task_count", 0),
        "owner": escape_table_cell(dag.get("owner", ""), 30),
        "schedule": escape_table_cell(dag.get("schedule", ""), 40),
    }


def _transform_error(err):
    """Convert an error into template-ready dict."""
    return {
        "rule": err["rule"],
        "file_name": os.path.basename(err.get("file", "")),
        "message": escape_table_cell(err.get("message", "")),
    }


def _transform_warning(warn):
    """Convert a warning into template-ready dict."""
    return {
        "rule": warn["rule"],
        "file_name": os.path.basename(warn.get("file", "")),
        "message": escape_table_cell(warn.get("message", "")),
    }


def _prepare_template_context(results, env_info="", custom_results=""):
    """Build context dict for the Jinja2 template."""
    passed = results["status"] == "pass"
    errors = results.get("errors", [])
    long_errors = [e for e in errors if len(e.get("message", "")) > 200]

    workflow = os.getenv("GITHUB_WORKFLOW", "")
    job = os.getenv("GITHUB_JOB", "")
    context_label = " • ".join(filter(None, (workflow, job)))

    return {
        "status_icon": "\u2705" if passed else "\u274c",
        "status_text": "All checks passed" if passed else "Validation failed",
        "context_label": context_label,
        "summary": results.get("summary", {}),
        "dags": [_transform_dag(d) for d in results.get("dags", [])],
        "errors": [_transform_error(e) for e in errors],
        "long_errors": long_errors,
        "warnings": [_transform_warning(w) for w in results.get("warnings", [])],
        "custom_results": (custom_results or "").strip(),
        "env_info": (env_info or "").strip(),
        "rules_applied": ", ".join(results.get("rules_applied", [])),
        "dag_dirs": ", ".join(results.get("dag_dirs", [])),
    }


def _load_template():
    """Load and return the Jinja2 template."""
    template_dir = Path(__file__).resolve().parent / "templates"
    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        autoescape=select_autoescape(default=False),
    )
    return env.get_template(TEMPLATE_NAME)


def format_markdown(results, env_info="", custom_results=""):
    """Render the PR comment from the Jinja2 template."""
    template = _load_template()
    context = _prepare_template_context(results, env_info, custom_results)
    return template.render(**context)


def _create_github_client(token):
    """Create a GitHub client from the given token."""
    try:
        return Github(auth=Auth.Token(token))
    except (TypeError, AttributeError):
        return Github(token)


def comment_pr(message):
    """Post the validation comment to the PR."""
    token = os.getenv("INPUT_ACCESSTOKEN", "")
    event_path = os.getenv("GITHUB_EVENT_PATH")

    if not event_path:
        print("GITHUB_EVENT_PATH not set, skipping PR comment.")
        print(message)
        return

    try:
        g = _create_github_client(token)
        repo = g.get_repo(os.getenv("GITHUB_REPOSITORY"))

        with open(event_path, encoding="utf-8") as f:
            payload = json.load(f)

        pr_number = payload.get("number")
        if pr_number is not None:
            repo.get_pull(pr_number).create_issue_comment(message)
        else:
            print("PR comment not supported on current event")
    except BadCredentialsException:
        print("Bad Credentials")
    except GithubException:
        print("Resource not accessible by integration")
    finally:
        print(message)


def main():
    results = load_json(RESULTS_FILE)
    if results is None:
        print(f"Results file not found: {RESULTS_FILE}")
        return

    env_info = read_file(ENV_INFO_FILE)
    custom_results = read_file(CUSTOM_RESULTS_FILE)

    message = format_markdown(results, env_info, custom_results)
    comment_pr(message)


if __name__ == "__main__":
    main()
