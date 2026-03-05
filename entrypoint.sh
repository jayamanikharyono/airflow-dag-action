#!/bin/bash
set -eo pipefail

echo "========================================="
echo " Airflow DAG Validation"
echo "========================================="
echo "Airflow version    : ${INPUT_AIRFLOWVERSION}"
echo "Python version     : ${INPUT_PYTHONVERSION}"
echo "Airflow extras     : ${INPUT_AIRFLOWEXTRAS}"
echo "DAGs directory     : ${INPUT_DAGPATHS}"
echo "Plugin directory   : ${INPUT_PLUGINPATHS}"
echo "Requirements       : ${INPUT_REQUIREMENTSFILE}"
echo "Variables file     : ${INPUT_VARFILE}"
echo "Connections file   : ${INPUT_CONNFILE}"
echo "Load examples      : ${INPUT_LOADEXAMPLES}"
echo "Validation rules   : ${INPUT_VALIDATIONRULES}"
echo "Max task count     : ${INPUT_MAXTASKCOUNT:-unlimited}"
echo "Custom tests       : ${INPUT_CUSTOMTESTS:-none}"
echo "Fail on error      : ${INPUT_FAILONERROR}"
echo "SARIF output       : ${INPUT_ENABLESARIF}"
echo "Diff-only mode     : ${INPUT_DIFFONLY:-false}"
echo "========================================="

# Set up pip cache directory for cross-run caching (P9)
export PIP_CACHE_DIR="${GITHUB_WORKSPACE}/.pip-cache"
mkdir -p "${PIP_CACHE_DIR}"

# Install Airflow
CONSTRAINT_URL="https://raw.githubusercontent.com/apache/airflow/constraints-${INPUT_AIRFLOWVERSION}/constraints-${INPUT_PYTHONVERSION}.txt"

if ! curl --head --silent --fail --output /dev/null "${CONSTRAINT_URL}" 2>/dev/null; then
    echo "::error::Constraint file not found: ${CONSTRAINT_URL}"
    echo "::error::Check that airflowVersion '${INPUT_AIRFLOWVERSION}' and pythonVersion '${INPUT_PYTHONVERSION}' are valid."
    exit 1
fi

echo "Installing Apache Airflow ${INPUT_AIRFLOWVERSION} [${INPUT_AIRFLOWEXTRAS}]..."
pip install \
    "apache-airflow[${INPUT_AIRFLOWEXTRAS}]==${INPUT_AIRFLOWVERSION}" \
    --constraint "${CONSTRAINT_URL}" && \
pip install --no-deps "apache-airflow[${INPUT_AIRFLOWEXTRAS}]==${INPUT_AIRFLOWVERSION}"

if [ -n "${INPUT_ADDITIONALPIPS}" ]; then
    echo "Installing additional packages: ${INPUT_ADDITIONALPIPS}"
    IFS=' ' read -ra PIP_PKGS <<< "${INPUT_ADDITIONALPIPS}"
    pip install "${PIP_PKGS[@]}"
fi

if [ -f "${INPUT_REQUIREMENTSFILE}" ]; then
    echo "Installing requirements from ${INPUT_REQUIREMENTSFILE}..."
    pip install -r "${INPUT_REQUIREMENTSFILE}"
else
    echo "Requirements file '${INPUT_REQUIREMENTSFILE}' not found, skipping."
fi

export AIRFLOW__CORE__LOAD_DEFAULT_CONNECTIONS="False"
export AIRFLOW__CORE__LOAD_EXAMPLES="${INPUT_LOADEXAMPLES}"

airflow db migrate || airflow db init

if [ -n "${INPUT_VARFILE}" ] && [ -f "${INPUT_VARFILE}" ]; then
    if ! python -m json.tool "${INPUT_VARFILE}" > /dev/null 2>&1; then
        echo "::error::Variables file '${INPUT_VARFILE}' is not valid JSON."
        exit 1
    fi
    echo "Importing variables from ${INPUT_VARFILE}..."
    airflow variables import "${INPUT_VARFILE}"
fi

if [ -n "${INPUT_CONNFILE}" ] && [ -f "${INPUT_CONNFILE}" ]; then
    if ! python -m json.tool "${INPUT_CONNFILE}" > /dev/null 2>&1; then
        echo "::error::Connections file '${INPUT_CONNFILE}' is not valid JSON."
        exit 1
    fi
    echo "Importing connections from ${INPUT_CONNFILE}..."
    airflow connections import "${INPUT_CONNFILE}"
fi

cp -r /action/* /github/workspace/

# Support multiple DAG directories (P8)
IFS=',' read -ra DAG_DIR_ARRAY <<< "${INPUT_DAGPATHS}"
for dag_dir in "${DAG_DIR_ARRAY[@]}"; do
    dag_dir=$(echo "${dag_dir}" | xargs)
    if [ -d "${dag_dir}" ]; then
        export PYTHONPATH="${PYTHONPATH:+${PYTHONPATH}:}${PWD}/${dag_dir}"
    fi
done
export AIRFLOW__CORE__PLUGINS_FOLDER="${PWD}/${INPUT_PLUGINPATHS}"

# Capture environment info for PR comment (skip on non-PR events)
if [ -n "${GITHUB_EVENT_PATH}" ]; then
    printf "List Variables:\n" > env_info.log
    airflow variables list >> env_info.log 2>&1
    printf "\nList Connections:\n" >> env_info.log
    airflow connections list >> env_info.log 2>&1
    printf "\nList Plugins:\n" >> env_info.log
    airflow plugins >> env_info.log 2>&1
fi

# Diff-aware validation: filter dagPaths to only changed directories
if [ "${INPUT_DIFFONLY}" = "true" ] && [ -n "${GITHUB_EVENT_PATH}" ]; then
    FILTERED=$(python diff_resolver.py 2>/dev/null || echo "${INPUT_DAGPATHS}")
    if [ -z "${FILTERED}" ]; then
        echo "Diff-only mode: no DAG files changed, skipping validation."
        [ -n "${GITHUB_OUTPUT}" ] && echo "validator-result=pass" >> "${GITHUB_OUTPUT}"
        exit 0
    elif [ "${FILTERED}" != "${INPUT_DAGPATHS}" ]; then
        echo "Diff-only mode: validating changed directories: ${FILTERED}"
        export INPUT_DAGPATHS="${FILTERED}"
    else
        echo "Diff-only mode: validating all directories (could not narrow scope)."
    fi
fi

# Run DAG validation
set +e
python dag_validation.py
validation_exit_code=$?
set -e

# Run custom tests if provided (P10)
custom_exit_code=0
if [ -n "${INPUT_CUSTOMTESTS}" ] && [ -f "${INPUT_CUSTOMTESTS}" ]; then
    echo ""
    echo "========================================="
    echo " Running Custom Tests"
    echo "========================================="
    set +e
    pytest "${INPUT_CUSTOMTESTS}" -v --tb=short 2>&1 | tee custom_results.log
    custom_exit_code=$?
    set -e
    echo "Custom tests exit code: ${custom_exit_code}"
fi

# Post structured PR comment (P6)
python alert.py

# Generate SARIF output
if [ "${INPUT_ENABLESARIF}" = "true" ]; then
    python sarif_output.py
    if [ -n "${GITHUB_OUTPUT}" ]; then
        echo "sarif-file=validation_results.sarif" >> "${GITHUB_OUTPUT}"
    fi
fi

# Expose JSON results as output
if [ -n "${GITHUB_OUTPUT}" ] && [ -f "validation_results.json" ]; then
    echo "results-json=validation_results.json" >> "${GITHUB_OUTPUT}"
fi

# Determine overall result
if [ ${validation_exit_code} -ne 0 ] || [ ${custom_exit_code} -ne 0 ]; then
    overall_exit_code=1
else
    overall_exit_code=0
fi

# Set outputs
if [ -n "${GITHUB_OUTPUT}" ]; then
    if [ ${overall_exit_code} -eq 0 ]; then
        echo "validator-result=pass" >> "${GITHUB_OUTPUT}"
    else
        echo "validator-result=fail" >> "${GITHUB_OUTPUT}"
    fi
fi

# Handle failOnError mode (P14)
if [ "${INPUT_FAILONERROR}" = "false" ]; then
    echo "failOnError is disabled, exiting with 0."
    exit 0
fi

exit "${overall_exit_code}"
