FROM python:3.7-slim-buster

ADD . /selected-tests
WORKDIR /selected-tests
RUN pip3 install .
RUN pip3 install gunicorn==19.9.0

CMD ["scripts/server.sh"]
