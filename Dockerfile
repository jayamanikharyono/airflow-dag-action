FROM python:3.7

ADD entrypoint.sh /entrypoint.sh
COPY . .

RUN pip install SQLAlchemy==1.3.23
RUN pip install Flask-SQLAlchemy==2.4.4
RUN pip install apache-airflow==1.10.12
RUN pip install google-cloud-storage
RUN pip install httplib2
RUN pip install google-auth-httplib2
RUN pip install google-api-python-client
RUN pip install pandas-gbq
RUN pip install pytest
RUN pip install PyGithub==1.55
RUN pip install -U WTForms==2.3.3


RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
