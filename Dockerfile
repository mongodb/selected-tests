FROM python:3.7-buster

RUN set -xe \
    apt-get install -y curl \
    apt-get install -y git

ADD . /selected-tests
WORKDIR /selected-tests
RUN pip3 install .

CMD ["scripts/server.sh"]
