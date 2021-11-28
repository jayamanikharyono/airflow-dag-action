FROM python:3.7

ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"


RUN pip3 install SQLAlchemy==1.3.23
RUN pip3 install Flask-SQLAlchemy==2.4.4
RUN pip3 install apache-airflow==1.10.12
RUN pip3 install httplib2==0.20.2
RUN pip3 install pytest==6.2.5
RUN pip3 install PyGithub==1.55
RUN pip3 install -U WTForms==2.3.3


# ADD entrypoint.sh /entrypoint.sh
COPY . /app
WORKDIR /app

RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
