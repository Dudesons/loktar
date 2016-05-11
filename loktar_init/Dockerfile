FROM ubuntu:16.04

RUN apt-get update && \
    apt-get install -y build-essential \
                       python-dev \
                       software-properties-common \
                       pkg-config \
                       gcc \
                       libfreetype6-dev \
                       libpng12-dev \
                       libjpeg-dev \
                       gfortran \
                       libatlas-base-dev \
                       liblapack-dev \
                       libopenblas-dev \
                       curl \
                       git && \
    curl --silent https://bootstrap.pypa.io/get-pip.py | python


COPY ./custom_lib/ /custom_libs/

RUN pip install -r /custom_libs/loktar/requirements.txt

ENV PYTHONPATH=$PYTHONPATH:/custom_libs/loktar/

COPY ./app /app

RUN pip install -r /app/requirements.txt

CMD python /app/lokworker/worker.py