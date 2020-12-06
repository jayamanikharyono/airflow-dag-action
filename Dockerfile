FROM python:3.6

ADD entrypoint.sh /entrypoint.sh

RUN pip install apache-airflow
RUN pip install google-cloud-storage
RUN pip install httplib2
RUN pip install google-auth-httplib2
RUN pip install google-api-python-client
RUN pip install pandas-gbq

ADD requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

ENV AIRFLOW_HOME=/github/workspace/airflow
ENV PYTHONPATH "${PYTHONPATH}:${AIRFLOW_HOME}"

RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
