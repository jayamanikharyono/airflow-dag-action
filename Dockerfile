FROM python:3.7

RUN python -m venv /opt/venv

# Install airflow
ENV PYTHON_VERSION 3.7
ENV AIRFLOW_VERSION=2.2.4
ENV CONSTRAINT_URL "https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt"
RUN pip install "apache-airflow[async,postgres,google,cncf.kubernetes]==${AIRFLOW_VERSION}" --constraint "${CONSTRAINT_URL}"

# Install Deps
RUN pip install google-cloud-storage
RUN pip install google-auth-httplib2
RUN pip install google-api-python-client
RUN pip install pandas-gbq
RUN pip install pytest
RUN pip install PyGithub==1.55

RUN mkdir /action
COPY dag_validation.py /action/dag_validation.py
COPY alert.py action/alert.py

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
