FROM python:3.7-slim-buster

RUN set -xe \
    apt-get install -y curl \
    apt-get install -y git

ADD . /selected-tests
WORKDIR /selected-tests
RUN pip3 install .
RUN pip3 install gunicorn==19.9.0

CMD ["scripts/server.sh"]
