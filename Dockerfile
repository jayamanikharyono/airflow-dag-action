FROM python:3.11

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir pytest PyGithub

RUN mkdir /action
COPY dag_validation.py /action/dag_validation.py
COPY alert.py /action/alert.py
COPY sarif_output.py /action/sarif_output.py

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
