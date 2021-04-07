FROM python:3.9-slim

MAINTAINER Michal Cernik "m.cernik@protonmail.com"

COPY holoarchive/ /app/holoarchive/
COPY ./app.py /app/main.py
COPY ./requirements.txt /app/requirements.txt
COPY ./docker_config.ini /persistent/config.ini

WORKDIR /app

EXPOSE 5000

RUN apt-get update -y
RUN apt-get install ffmpeg -y
RUN apt-get autoremove -y
#RUN apt install gcc g++ make libffi-dev openssl-dev ffmpeg
#RUN apt install atomicparsley
RUN pip install -r /app/requirements.txt

ENV HOLOARCHIVE_CONFIG=/persistent/config.ini
ENV HOLOARCHIVE_DB=/persistent/db.sqlite
ENV PATH /usr/bin/ffmpeg:$PATH

ENTRYPOINT [ "python" ]
CMD [ "main.py" ]