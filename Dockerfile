FROM python:3.7-buster

RUN set -xe \
    apt-get install -y curl \
    apt-get install -y git

RUN pip3 install --upgrade pip
RUN pip3 install poetry

ADD . /selected-tests
WORKDIR /selected-tests
RUN poetry install

CMD ["scripts/server.sh"]
