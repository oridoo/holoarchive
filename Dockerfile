FROM tiangolo/meinheld-gunicorn-flask:python3.8-alpine3.11

COPY holoarchive/ /app/holoarchive/
COPY ./app.py /app/main.py
COPY ./requirements.txt /app/requirements.txt
COPY ./docker_config.ini /persistent/config.ini

RUN apk add gcc g++ make libffi-dev openssl-dev chromium-chromedriver ffmpeg
RUN pip install -r /app/requirements.txt

ENV HOLOARCHIVE_CONFIG=/persistent/config.ini
ENV HOLOARCHIVE_DB=/persistent/db.sqlite





