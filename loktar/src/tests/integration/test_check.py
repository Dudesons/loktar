import pytest

from loktar.check import wait_dynamodb
from loktar.check import wait_elasticsearch
from loktar.check import wait_etcd
from loktar.check import wait_mongo
from loktar.check import wait_rds
from loktar.check import wait_redis
from loktar.check import wait_s3
from loktar.check import wait_sqs
from loktar.check import wait_ssh


def test_wait_dynamodb():
    assert wait_dynamodb(host="dynamodb") is True


def test_wait_elasticsearch():
    is_ready = wait_elasticsearch(host="elasticsearch")

    assert is_ready is True


def test_wait_etcd():
    is_ready = wait_etcd(host="etcd")

    assert is_ready is True


def test_wait_mongo():
    is_ready = wait_mongo(host="mongo")

    assert is_ready is True


def test_wait_redis():
    is_ready = wait_redis(host="redis")

    assert is_ready is True


def test_wait_sqs():
    assert wait_sqs(host="sqs", fake_region="loktar") is True

"""
def test_wait_ssh():
    is_ready = wait_ssh(host="ssh")

    assert is_ready is True
"""

def test_wait_s3():
    assert wait_s3(host="s3") is True

"""
def test_wait_rds():
    assert wait_rds(host="rds") is True
"""