FROM python:3.7

RUN python -m venv /opt/venv

# Install airflow
ENV PYTHON_VERSION 3.7
ENV AIRFLOW_VERSION=2.2.4
ENV CONSTRAINT_URL "https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt"
RUN pip install "apache-airflow[async,postgres,google]==${AIRFLOW_VERSION}" --constraint "${CONSTRAINT_URL}"

# Install Deps
RUN pip install google-cloud-storage
RUN pip install google-auth-httplib2
RUN pip install google-api-python-client
RUN pip install pandas-gbq
RUN pip install pytest
RUN pip install PyGithub==1.55
RUN pip install Unidecode

ADD entrypoint.sh /entrypoint.sh
ADD dag_validation.py /dag_validation.py
ADD alert.py /alert.py

RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
