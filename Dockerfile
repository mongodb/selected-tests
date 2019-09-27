FROM ubuntu:18.04
RUN set -xe \
    && apt-get update \
    && apt-get install -y curl gcc g++ \
    && apt-get install -y python3-dev \
    && apt-get install -y libffi-dev \
    && apt-get install -y libssl-dev \
    && apt-get install -y python3-pip \
    && apt-get install -y git
RUN pip3 install --upgrade pip

ADD . /selected-tests
WORKDIR /selected-tests
RUN pip3 install -r requirements.txt
RUN pip3 install .

CMD ["scripts/server.sh"]
