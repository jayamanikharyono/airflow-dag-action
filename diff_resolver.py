# -*- coding: utf-8 -*-
"""
Diff-aware DAG directory filtering.

Determines which dagPaths directories contain changed files so that
unchanged directories can be skipped, speeding up CI in monorepos.

Strategy 1 (PRs):  GitHub API /pulls/{number}/files  — works with shallow clones.
Strategy 2 (pushes): git diff with automatic shallow-fetch of the base SHA.
Fallback: outputs the original dagPaths unchanged.

@author: jayaharyonomanik
"""

import json
import os
import subprocess
import sys
from urllib.error import URLError
from urllib.request import Request, urlopen


def _read_event(event_path):
    """Read and parse the GitHub Actions event payload."""
    if not event_path or not os.path.isfile(event_path):
        return {}
    with open(event_path, encoding="utf-8") as f:
        return json.load(f)


def _get_pr_number(event):
    """Extract the pull request number from the event payload."""
    num = event.get("number") or event.get("pull_request", {}).get("number")
    if num and int(num) > 0:
        return int(num)
    return None


def _get_base_sha(event):
    """Extract the base SHA for diffing (PR base or push 'before')."""
    sha = event.get("pull_request", {}).get("base", {}).get("sha", "")
    if not sha:
        sha = event.get("before", "")
    if sha and sha != "0" * 40:
        return sha
    return None


def _fetch_pr_files_via_api(repo, pr_number, token):
    """Fetch changed filenames from the GitHub Pull Request Files API.

    Handles pagination (100 per page, up to 3000 files max by GitHub).
    Returns a list of filenames or None on failure.
    """
    all_files = []
    page = 1
    while True:
        url = (
            f"https://api.github.com/repos/{repo}/pulls/{pr_number}"
            f"/files?per_page=100&page={page}"
        )
        req = Request(url, headers={
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
        })
        try:
            with urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())
        except (URLError, json.JSONDecodeError, OSError):
            return None

        if not isinstance(data, list) or not data:
            break

        all_files.extend(f.get("filename", "") for f in data)

        if len(data) < 100:
            break
        page += 1

    return all_files if all_files else None


def _fetch_changed_files_via_git(base_sha):
    """Get changed filenames via git diff, fetching the base SHA if needed."""
    try:
        subprocess.run(
            ["git", "cat-file", "-e", base_sha],
            check=True, capture_output=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        try:
            subprocess.run(
                ["git", "fetch", "--no-tags", "--depth=1", "origin", base_sha],
                capture_output=True, timeout=60,
            )
        except (subprocess.SubprocessError, FileNotFoundError):
            return None

    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", f"{base_sha}..HEAD"],
            capture_output=True, text=True, timeout=60,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip().splitlines()
    except (subprocess.SubprocessError, FileNotFoundError):
        pass

    return None


def get_changed_files():
    """Return a list of changed filenames, or None if undetermined."""
    event_path = os.getenv("GITHUB_EVENT_PATH", "")
    token = os.getenv("INPUT_ACCESSTOKEN", "")
    repo = os.getenv("GITHUB_REPOSITORY", "")

    event = _read_event(event_path)
    if not event:
        return None

    pr_number = _get_pr_number(event)
    if pr_number and token and repo:
        files = _fetch_pr_files_via_api(repo, pr_number, token)
        if files is not None:
            return files

    base_sha = _get_base_sha(event)
    if base_sha:
        files = _fetch_changed_files_via_git(base_sha)
        if files is not None:
            return files

    return None


def filter_dag_paths(dag_paths_csv, changed_files):
    """Return comma-separated dagPaths filtered to only changed directories.

    Returns:
        str: filtered dagPaths CSV, or empty string if none matched.
    """
    dirs = [d.strip() for d in dag_paths_csv.split(",") if d.strip()]
    filtered = [d for d in dirs if any(f.startswith(d + "/") for f in changed_files)]
    return ",".join(filtered)


def main():
    """Print filtered dagPaths to stdout.

    Output cases:
      - Filtered CSV   → only changed directories
      - Empty string    → no DAG dirs changed (caller should skip validation)
      - Original CSV    → could not determine changes (caller should validate all)
    """
    dag_paths = os.getenv("INPUT_DAGPATHS", "dags")

    changed_files = get_changed_files()
    if changed_files is None:
        print(dag_paths)
        return

    filtered = filter_dag_paths(dag_paths, changed_files)
    print(filtered)


if __name__ == "__main__":
    main()
