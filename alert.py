# -*- coding: utf-8 -*-
"""
@author: jayaharyonomanik
"""

import os
import json
from github import Github
from github.GithubException import GithubException, BadCredentialsException


def escape_table_cell(text, max_len=200):
    """Escape and truncate text for use in Markdown table cells."""
    text = str(text).replace("|", "\\|").replace("\n", " ").replace("\r", "")
    if len(text) > max_len:
        text = text[:max_len] + "..."
    return text


def format_markdown(results, env_info="", custom_results=""):
    status_icon = "\u2705" if results["status"] == "pass" else "\u274c"
    status_text = "All checks passed" if results["status"] == "pass" else "Validation failed"
    summary = results.get("summary", {})

    lines = [
        "## Airflow DAG Validation Results",
        "",
        f"**Status:** {status_icon} {status_text}",
        (
            f"**DAGs:** {summary.get('total_dags', 0)} | "
            f"**Errors:** {summary.get('total_errors', 0)} | "
            f"**Warnings:** {summary.get('total_warnings', 0)}"
        ),
        "",
    ]

    dags = results.get("dags", [])
    if dags:
        lines.append("### DAGs")
        lines.append("| DAG ID | File | Tasks | Owner | Schedule |")
        lines.append("|--------|------|-------|-------|----------|")
        for dag in dags:
            dag_id = escape_table_cell(dag["dag_id"], 60)
            file_name = os.path.basename(dag.get("file", ""))
            schedule = escape_table_cell(dag.get("schedule", ""), 40)
            owner = escape_table_cell(dag.get("owner", ""), 30)
            lines.append(
                f"| `{dag_id}` | `{file_name}` "
                f"| {dag.get('task_count', 0)} | {owner} | `{schedule}` |"
            )
        lines.append("")

    errors = results.get("errors", [])
    if errors:
        lines.append(f"### Errors ({len(errors)})")
        lines.append("| Rule | File | Message |")
        lines.append("|------|------|---------|")
        for err in errors:
            lines.append(
                f"| `{err['rule']}` | `{os.path.basename(err['file'])}` "
                f"| {escape_table_cell(err['message'])} |"
            )
        lines.append("")

        long_errors = [e for e in errors if len(e.get("message", "")) > 200]
        if long_errors:
            lines.append("<details>")
            lines.append("<summary>Full Error Details</summary>")
            lines.append("")
            for err in long_errors:
                lines.append(f"**[{err['rule']}] `{err['file']}`**")
                lines.append("```")
                lines.append(err["message"])
                lines.append("```")
                lines.append("")
            lines.append("</details>")
            lines.append("")

    warnings = results.get("warnings", [])
    if warnings:
        lines.append(f"### Warnings ({len(warnings)})")
        lines.append("| Rule | File | Message |")
        lines.append("|------|------|---------|")
        for warn in warnings:
            lines.append(
                f"| `{warn['rule']}` | `{os.path.basename(warn['file'])}` "
                f"| {escape_table_cell(warn['message'])} |"
            )
        lines.append("")

    if custom_results:
        lines.append("<details>")
        lines.append("<summary>Custom Test Results</summary>")
        lines.append("")
        lines.append("```")
        lines.append(custom_results.strip())
        lines.append("```")
        lines.append("</details>")
        lines.append("")

    if env_info:
        lines.append("<details>")
        lines.append("<summary>Environment Details</summary>")
        lines.append("")
        lines.append("```")
        lines.append(env_info.strip())
        lines.append("```")
        lines.append("</details>")
        lines.append("")

    rules = results.get("rules_applied", [])
    dirs = results.get("dag_dirs", [])
    lines.append(f"<sub>Rules: {', '.join(rules)} | Dirs: {', '.join(dirs)}</sub>")

    return "\n".join(lines)


def comment_pr(message):
    repo_token = os.getenv("INPUT_ACCESSTOKEN", "")

    try:
        g = Github(repo_token)
        repo = g.get_repo(os.getenv("GITHUB_REPOSITORY"))
        event_path = os.getenv("GITHUB_EVENT_PATH")
        if not event_path:
            print("GITHUB_EVENT_PATH not set, skipping PR comment.")
            return

        with open(event_path, encoding="utf-8") as f:
            json_payload = json.load(f)

        pr_number = json_payload.get("number")
        if pr_number is not None:
            pr = repo.get_pull(pr_number)
            pr.create_issue_comment(message)
        else:
            print("PR comment not supported on current event")
    except BadCredentialsException as bce:
        print("Bad Credentials")
        print(bce.args)
    except GithubException as ge:
        print("Resource not accessible by integration")
        print(ge.args)
    finally:
        print(message)


def main():
    results_file = "validation_results.json"
    env_info_file = "env_info.log"
    custom_results_file = "custom_results.log"

    if not os.path.isfile(results_file):
        print(f"Results file not found: {results_file}")
        return

    with open(results_file, encoding="utf-8") as f:
        results = json.load(f)

    env_info = ""
    if os.path.isfile(env_info_file):
        with open(env_info_file, encoding="utf-8") as f:
            env_info = f.read()

    custom_results = ""
    if os.path.isfile(custom_results_file):
        with open(custom_results_file, encoding="utf-8") as f:
            custom_results = f.read()

    message = format_markdown(results, env_info, custom_results)
    comment_pr(message)


if __name__ == "__main__":
    main()
