FROM python:3.7

ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"


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


# ADD entrypoint.sh /entrypoint.sh
COPY . /app
WORKDIR /app

RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
