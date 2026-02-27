# Airflow DAG Action - Code Review & Improvement Proposals

## Table of Contents

- [Overview](#overview)
- [Part 1: Bugs & Issues Found](#part-1-bugs--issues-found)
- [Part 2: Code Quality Concerns](#part-2-code-quality-concerns)
- [Part 3: Improvement Proposals](#part-3-improvement-proposals)
- [Changelog](#changelog)

---

## Overview

This review covers the `airflow-dag-action` GitHub Action — a Docker-based action that validates Airflow DAGs, variables, connections, and plugins in an isolated environment, with PR comment reporting.

**Reviewed files:** `action.yml`, `Dockerfile`, `entrypoint.sh`, `dag_validation.py`, `alert.py`, `README.md`, CI workflows, and test fixtures.

---

## Part 1: Bugs & Issues Found

### 1.1 ~~Broken Action Output~~ FIXED

**File:** `action.yml`

`steps.run` referenced a step ID that did not exist. Docker-based actions don't expose internal step IDs to the caller. Output was always empty.

**Fix:** Removed invalid `value` reference. Entrypoint now writes to `$GITHUB_OUTPUT` so consumers can access the result via `steps.<id>.outputs.validator-result`.

---

### 1.2 ~~Variable/Connection Import Fails on Empty Paths~~ FIXED

**File:** `entrypoint.sh`

When `varFile` or `connFile` were empty (their defaults), the import commands ran with no argument and errored.

**Fix:** Added `[ -n "..." ] && [ -f "..." ]` guards. Import only runs when a non-empty path is provided and the file actually exists.

---

### 1.3 ~~Fragile Exit Code Handling~~ FIXED

**File:** `entrypoint.sh`

Exit code was captured as a human-readable string and string-compared.

**Fix:** Now uses `set +e` / `set -e` around pytest, captures `$?` as a numeric variable, and uses it directly for `exit`.

---

### 1.4 ~~No Requirements File Existence Check~~ FIXED

**File:** `entrypoint.sh`

**Fix:** Added `[ -f "${INPUT_REQUIREMENTSFILE}" ]` guard. Prints a skip message if the file doesn't exist.

---

### 1.5 ~~Missing `set -e` / Error Handling~~ FIXED

**File:** `entrypoint.sh`

**Fix:** Added `set -eo pipefail` at the top. Intermediate command failures now cause immediate exit with a clear error.

---

## Part 2: Code Quality Concerns

### 2.1 ~~Outdated Dependencies~~ FIXED

| Component | Before | After |
|---|---|---|
| Python | 3.8 (EOL) | 3.11 |
| Apache Airflow | 2.2.4 (hardcoded) | User-configurable (default: 2.10.4) |
| PyGithub | 1.55 (pinned) | Latest (unpinned) |
| `actions/checkout` | v2 | v4 |

---

### 2.2 ~~Dockerfile Inefficiencies~~ FIXED

**Before:** 6 separate `RUN pip install` layers, no `.dockerignore`, Airflow + GCP libs baked in.

**After:** Single combined `RUN` layer with only core tools (pytest, PyGithub). Airflow installed at runtime based on user inputs. `.dockerignore` added to exclude `.git`, `tests/`, `images/`, docs.

---

### 2.3 ~~Hardcoded Google Cloud Dependencies~~ FIXED

GCP-specific packages (`google-cloud-storage`, `google-auth-httplib2`, `google-api-python-client`, `pandas-gbq`) removed from the base image. Users who need them can add them via the new `airflowExtras` input (e.g. `"async,postgres,google"`) or `additionalPips`.

---

### 2.4 ~~File Handle Leak in `alert.py`~~ FIXED

**Fix:** Both file reads now use `with` statements. Removed the `encode("ascii", "ignore")` call that silently stripped non-ASCII characters.

---

### 2.5 ~~PR Comment Formatting~~ FIXED

**Fix:** Complete rewrite of `alert.py`. PR comments now use structured Markdown with status indicators, DAG tables, error/warning tables, collapsible sections for environment details and custom test results.

---

### 2.6 ~~Unquoted Variables in Shell Script~~ FIXED

**Fix:** Switched from positional args (`$1`, `$2`, ...) to `INPUT_*` environment variables (automatically set by GitHub Actions for Docker actions). All variable references are now properly quoted.

---

### 2.7 ~~Sensitive Token Passed as CLI Argument~~ FIXED

**Fix:** Token is no longer passed as a CLI argument. `alert.py` reads it directly from the `INPUT_ACCESSTOKEN` environment variable set by GitHub Actions.

---

## Part 3: Improvement Proposals

### P1: ~~Configurable Airflow & Python Versions~~ DONE

**Implemented.** New inputs added to `action.yml`:

| Input | Default | Description |
|---|---|---|
| `airflowVersion` | `"2.10.4"` | Apache Airflow version to install |
| `pythonVersion` | `"3.11"` | Python version for constraint resolution |

Airflow is now installed at runtime in `entrypoint.sh` using the configured version and the corresponding Apache constraint file. The base Docker image uses Python 3.11. Full Python version flexibility (changing the base image) is available through pre-built images (P2).

---

### P2: ~~Pre-built Docker Images for Faster CI~~ DONE

**Implemented.** Infrastructure added:

- **`Dockerfile.prebuilt`** — Parameterized Dockerfile that bakes Airflow into the image at build time via `ARG` (Python version, Airflow version, extras).
- **`.github/workflows/build-images.yml`** — CI workflow that builds and pushes images to GHCR for a matrix of versions (Airflow 2.9.3/2.10.4 x Python 3.11/3.12). Triggers on changes to core files or manual dispatch.

**Image tags:** `ghcr.io/<repo>:py3.11-af2.10.4`, `ghcr.io/<repo>:py3.12-af2.9.3`, etc.

**Usage in custom workflows:** Users can reference pre-built images directly in their own workflows using `docker run` for faster CI, bypassing the Dockerfile build step. The default action still builds from the local `Dockerfile` for zero-config usage.

---

### P3: ~~Configurable Airflow Provider Packages~~ DONE

**Implemented.** New inputs added to `action.yml`:

| Input | Default | Description |
|---|---|---|
| `airflowExtras` | `"async,postgres"` | Comma-separated Airflow extras (e.g. `"async,postgres,google,cncf.kubernetes"`) |
| `additionalPips` | `""` | Space-separated arbitrary pip packages (e.g. `"numpy pandas boto3"`) |

GCP-specific packages removed from the base image. Users opt into exactly what they need.

---

### P4: ~~Fix and Improve Shell Script Robustness~~ DONE

**Implemented.** All fixes from Part 1 applied:

- `set -eo pipefail` at the top
- `INPUT_*` env vars instead of positional args (no more unquoted `$1`..`$7`)
- Guard checks for empty/missing `varFile`, `connFile`, and `requirementsFile`
- Numeric exit code handling with `set +e`/`set -e` around pytest
- Token read from env var, not CLI arg
- `airflow db migrate || airflow db init` for compatibility across Airflow versions
- Proper `printf` instead of `echo "\n"`

---

### P5: ~~Enhanced DAG Validation Tests~~ DONE

**Implemented.** Complete rewrite of `dag_validation.py` from a unittest-based script to a standalone validation engine with structured JSON output.

**Validation rules available** (configured via `validationRules` input, default: `"all"`):

| Rule | Type | Description |
|---|---|---|
| `import` | Error | DAG file failed to import (syntax errors, missing deps) |
| `cycle` | Error | DAG has circular task dependencies (Kahn's algorithm) |
| `duplicates` | Error | Multiple DAGs share the same `dag_id` |
| `task_count` | Warning | DAG exceeds `maxTaskCount` threshold |
| `owner` | Warning | DAG has no meaningful owner (empty or "airflow") |
| `empty_dag` | Warning | DAG has zero tasks |

**New inputs:** `validationRules` (default: `"all"`), `maxTaskCount` (default: `""` = no limit).

**Architecture change:** Validation now outputs structured JSON (`validation_results.json`) consumed by `alert.py` and `sarif_output.py`, replacing the previous raw log piping.

---

### P6: ~~Better PR Comment Formatting~~ DONE

**Implemented.** Complete rewrite of `alert.py` to generate structured Markdown PR comments:

- Status header with pass/fail indicator
- DAG summary table (DAG ID, file, task count, owner, schedule)
- Error table with rule, file, and truncated message
- Collapsible full error details for long tracebacks
- Warning table
- Collapsible custom test results (if P10 custom tests ran)
- Collapsible environment details (variables, connections, plugins)
- Footer with applied rules and validated directories

Table cell content is escaped (pipes, newlines) and truncated to prevent formatting issues.

---

### P7: ~~GitHub Actions Annotations~~ DONE

**Implemented.** `dag_validation.py` now emits GitHub Actions workflow commands for file-level annotations:

- `::error file=<path>,title=DAG Validation (<rule>)::<message>` for errors
- `::warning file=<path>,title=DAG Validation (<rule>)::<message>` for warnings

These appear inline on PR diffs and in the Actions summary, making it immediately visible which files have issues without opening the PR comment.

---

### P8: ~~Support for Multiple DAG Directories~~ DONE

**Implemented.** The `dagPaths` input now accepts comma-separated paths: `dagPaths: "dags/etl,dags/ml,dags/reporting"`.

- `entrypoint.sh` splits the input by comma and adds each directory to `PYTHONPATH`
- `dag_validation.py` iterates over each directory, loading a separate `DagBag` per directory
- Duplicate DAG ID detection works across all directories
- PR comment footer shows all validated directories

---

### P9: ~~Dependency Caching~~ DONE

**Implemented.** The entrypoint now sets `PIP_CACHE_DIR` to `${GITHUB_WORKSPACE}/.pip-cache`, a location shared between the Docker container and the host runner. Pip commands no longer use `--no-cache-dir`, enabling caching.

**Cross-run caching** requires adding `actions/cache` in the caller's workflow:

```yaml
- uses: actions/cache@v4
  with:
    path: .pip-cache
    key: pip-${{ hashFiles('requirements.txt') }}
    restore-keys: pip-
```

The CI workflow (`main.yml`) demonstrates this pattern.

---

### P10: ~~Custom Validation Scripts~~ DONE

**Implemented.** New `customTests` input accepts a path to a user's own pytest file. The entrypoint runs built-in validation first, then custom tests via `pytest` with verbose output.

- Custom test output is captured to `custom_results.log`
- Results appear in the PR comment under a collapsible "Custom Test Results" section
- Custom test failures contribute to the overall exit code
- Works with `failOnError: "false"` (P14) for warning-only mode

---

### P12: ~~SARIF Output for GitHub Code Scanning~~ DONE

**Implemented.** New `sarif_output.py` generates SARIF 2.1.0 output from validation results.

- Enabled via `enableSarif: "true"` input
- Outputs `validation_results.sarif` to the workspace
- File path available via `sarif-file` output for upload
- Maps validation errors to `error` level and warnings to `warning` level
- Each validation rule becomes a SARIF rule with descriptive metadata
- File paths are relative to `%SRCROOT%` for proper GitHub rendering

**Usage with code scanning:**

```yaml
- name: Upload SARIF
  if: always() && steps.validate.outputs.sarif-file != ''
  uses: github/codeql-action/upload-sarif@v3
  with:
    sarif_file: validation_results.sarif
    category: airflow-dag-validation
```

The CI workflow demonstrates this integration.

---

### P14: ~~Dry-Run / Warning-Only Mode~~ DONE

**Implemented.** New `failOnError` input (default: `"true"`).

When set to `"false"`, the action posts all results (PR comment, annotations, SARIF) but always exits with code 0, preventing the workflow from failing. Useful for:
- Initial adoption (see results without blocking PRs)
- Informational-only validation in non-critical branches
- Gradual rollout of new validation rules

---

### P15: ~~Add `.dockerignore`~~ DONE

**Implemented.** `.dockerignore` added, excluding `.git`, `.github`, `tests/`, `images/`, `*.md`, and `LICENSE` from the Docker build context.

---

## Summary & Priority Matrix

| # | Proposal | Priority | Complexity | Status |
|---|---|---|---|---|
| P1 | Configurable Airflow & Python versions | High | Medium | **DONE** (Phase 1) |
| P2 | Pre-built Docker images (GHCR) | High | Medium | **DONE** (Phase 1) |
| P3 | Configurable provider packages | High | Low-Med | **DONE** (Phase 1) |
| P4 | Shell script robustness fixes | High | Low | **DONE** (Phase 1) |
| P5 | Enhanced DAG validation rules | Medium | Medium | **DONE** (Phase 2) |
| P6 | Better PR comment formatting | Medium | Medium | **DONE** (Phase 2) |
| P7 | GitHub Actions annotations | Medium | Low | **DONE** (Phase 2) |
| P8 | Multiple DAG directories | Low-Med | Low | **DONE** (Phase 2) |
| P9 | Dependency caching | Low-Med | Medium | **DONE** (Phase 2) |
| P10 | Custom validation scripts | Low | Low | **DONE** (Phase 2) |
| P12 | SARIF output for code scanning | Low | Medium | **DONE** (Phase 2) |
| P14 | Dry-run / warning-only mode | Low | Low | **DONE** (Phase 2) |
| P15 | Add `.dockerignore` | Low | Trivial | **DONE** (Phase 1) |

### All Proposals Completed

All 13 proposals have been implemented across Phase 1 and Phase 2. P11 and P13 were dropped from scope.

---

## Changelog

### Phase 1 — High Priority (Completed)

**Bug Fixes:**
- Fixed broken `validator-result` output (now uses `$GITHUB_OUTPUT`)
- Fixed empty `varFile`/`connFile` crashing the action
- Fixed missing requirements file crashing the action
- Fixed fragile string-based exit code handling (now numeric)
- Added `set -eo pipefail` for proper error propagation
- Fixed file handle leaks in `alert.py`
- Fixed `BadCredentialsException` handler being dead code (was shadowed by parent `GithubException` catch)
- Removed silent Unicode stripping (`encode("ascii", "ignore")`)
- Token no longer exposed as CLI argument

**Features:**
- `airflowVersion` input — validate against any Airflow version (default: 2.10.4)
- `pythonVersion` input — constraint resolution for the target Python version (default: 3.11)
- `airflowExtras` input — choose exactly which Airflow providers to install (default: `async,postgres`)
- `additionalPips` input — install arbitrary pip packages
- Pre-built image infrastructure via `Dockerfile.prebuilt` + GHCR build workflow
- `.dockerignore` for faster Docker builds

**Infrastructure:**
- Base image updated from Python 3.8 to 3.11
- Dockerfile slimmed down (Airflow installed at runtime for configurability)
- Switched from positional shell args to `INPUT_*` environment variables
- `actions/checkout` updated from v2 to v4
- `airflow db migrate` with fallback to `db init` for cross-version compatibility
- CI workflow updated to demonstrate new inputs (`airflowVersion`, `airflowExtras`, `additionalPips`)

**Files changed:** `action.yml`, `Dockerfile`, `entrypoint.sh`, `alert.py`, `.github/workflows/main.yml`
**Files added:** `.dockerignore`, `Dockerfile.prebuilt`, `.github/workflows/build-images.yml`

---

### Phase 2 — Medium & Low Priority (Completed)

**Major Rewrites:**
- `dag_validation.py` — Complete rewrite from unittest to standalone validation engine with JSON output, configurable rules, cycle detection (Kahn's algorithm), and GitHub Actions annotation emission
- `alert.py` — Complete rewrite from raw code block dump to structured Markdown with tables, collapsible sections, and multi-source input (validation JSON + env info + custom test results)

**New Features:**
- `validationRules` input — Select which rules to run: `import`, `cycle`, `duplicates`, `task_count`, `owner`, `empty_dag`, or `"all"` (default)
- `maxTaskCount` input — Configurable task count threshold for warnings
- `customTests` input — Run user-provided pytest files alongside built-in validation
- `failOnError` input — Warning-only mode when set to `"false"` (action posts results but exits 0)
- `enableSarif` input — Generate SARIF 2.1.0 output for GitHub code scanning integration
- Multiple DAG directories via comma-separated `dagPaths`
- File-level GitHub Actions annotations for errors and warnings
- Pip cache directory under workspace for cross-run caching with `actions/cache`

**New Outputs:**
- `validator-result` now outputs `pass`/`fail` (was numeric exit code)
- `sarif-file` — Path to generated SARIF file (when `enableSarif` is enabled)

**CI Workflow Updates:**
- Added `actions/cache` step for pip package caching
- Added SARIF upload step via `github/codeql-action/upload-sarif@v3`
- Demonstrates new inputs: `validationRules`, `enableSarif`

**Files changed:** `dag_validation.py`, `alert.py`, `entrypoint.sh`, `action.yml`, `Dockerfile`, `Dockerfile.prebuilt`, `.github/workflows/main.yml`, `.github/workflows/build-images.yml`
**Files added:** `sarif_output.py`
