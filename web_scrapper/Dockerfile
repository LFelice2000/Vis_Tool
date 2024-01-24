FROM ubuntu:latest

WORKDIR /app

COPY requirements.txt ./

RUN apt-get -y update && apt-get install -y build-essential && apt install -y python3-dev libpq-dev && apt-get install -y python3-pip\
    && pip install -r ./requirements.txt && apt-get -y install git && apt-get -y install wget && apt-get -y install curl && apt-get -y install unzip\
    && pip install django_extensions

# Install Chrome WebDriver
RUN CHROMEDRIVER_VERSION=`curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE` && \
    mkdir -p /opt/chromedriver-$CHROMEDRIVER_VERSION && \
    curl -sS -o /tmp/chromedriver_linux64.zip http://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip && \
    unzip -qq /tmp/chromedriver_linux64.zip -d /opt/chromedriver-$CHROMEDRIVER_VERSION && \
    rm /tmp/chromedriver_linux64.zip && \
    chmod +x /opt/chromedriver-$CHROMEDRIVER_VERSION/chromedriver && \
    ln -fs /opt/chromedriver-$CHROMEDRIVER_VERSION/chromedriver /usr/local/bin/chromedriver

# Install Google Chrome
RUN curl -sS -o - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list && \
    apt-get -yqq update && \
    apt-get -yqq install google-chrome-stable && \
    rm -rf /var/lib/apt/lists/*

COPY ./ ./

RUN mkdir -p certs/

COPY /etc/letsencrypt/live/nabu.ii.uam.es/privkey.pem certs/
COPY /etc/letsencrypt/live/nabu.ii.uam.es/fullchain.pem certs/

ENV DISPLAY=:99

EXPOSE 8000