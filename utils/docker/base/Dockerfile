FROM ubuntu:16.04

RUN apt-get update && \
    apt-get install -y python-dev curl && \
    curl --silent --show-error --retry 5 https://bootstrap.pypa.io/get-pip.py | python && \
    apt-get install -y pkg-config \
                       gfortran \
                       libopenblas-dev \
                       liblapack-dev \
                       libfreetype6-dev \
                       libpng12-dev \
                       libssl-dev \
                       libffi-dev \
                       libyaml-dev \
                       make && \
    apt-get remove -y python-pycparser && \
    apt-get install g++ -y

COPY requirements.txt /base-components/requirements.txt

RUN pip install -r /base-components/requirements.txt

COPY entrypoint.sh /

RUN chmod 100 /entrypoint.sh
