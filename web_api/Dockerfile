FROM ubuntu:latest

WORKDIR /app

COPY ./requirements.txt ./

RUN apt-get -y update && apt-get install -y build-essential && apt install -y python3-dev libpq-dev && apt-get install -y python3-pip\
    && pip install -r ./requirements.txt && apt-get -y install git && apt-get -y install wget && apt-get -y install curl && apt-get -y install unzip\
    && pip install django_extensions

COPY ./ ./

ENV DISPLAY=:99

EXPOSE 8080