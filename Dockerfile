ARG PYTHON_VERSION=3.9.10

FROM python:${PYTHON_VERSION}

RUN apt-get update && apt-get install -y \
    postgresql-contrib \
    redis-tools \
    python3-pip \
    python3-venv \
    python3-dev \
    python3-setuptools \
    python3-wheel


RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
RUN sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'
RUN apt-get -y update
RUN apt-get install -y google-chrome-stable

RUN apt-get install -yqq unzip
RUN wget -O /tmp/chromedriver.zip http://chromedriver.storage.googleapis.com/`curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE`/chromedriver_linux64.zip
RUN unzip /tmp/chromedriver.zip chromedriver -d /usr/local/bin/
ENV DISPLAY=:99


RUN mkdir -p /app
WORKDIR /app
COPY requirements.txt .
RUN python -m pip install --upgrade pip
RUN pip install -r requirements.txt
COPY . .

EXPOSE 8080 44300
ENTRYPOINT honcho start 
