import pytest

from etcd import EtcdException
import paramiko
import requests
import socket

from loktar.check import wait_dynamodb
from loktar.check import wait_elasticsearch
from loktar.check import wait_etcd
from loktar.check import wait_mongo
from loktar.check import wait_rds
from loktar.check import wait_redis
from loktar.check import wait_s3
from loktar.check import wait_sqs
from loktar.check import wait_ssh

from loktar.check import requests as mp_requests


@pytest.mark.parametrize("fail", [True, False])
def test_wait_dynamodb(mocker, fail):
    class FakeDDB(object):
        def __init__(self, *args, **kwargs):
            pass
        
        def list_tables(self):
            if fail:
                raise socket.gaierror
            else:
                return list()
    
    mocker.patch("loktar.check.ddb_connect_to_region", return_value=FakeDDB())

    if fail:
        assert wait_dynamodb() is False
    else:
        assert wait_dynamodb() is True


@pytest.mark.parametrize("fail", [True, False])
def test_wait_elasticsearch(monkeypatch, fail):
    class FakeResponse(object):
        def __init__(self):
            pass

        def json(self):
            return {
                "status": "green"
            }

    def fake_request(*args, **kwargs):
        if fail:
            def t():
                raise requests.exceptions.ConnectionError
            return t()
        else:
            return FakeResponse()

    monkeypatch.setattr(mp_requests, "get", lambda *args, **kwargs: fake_request())

    is_ready = wait_elasticsearch(retries=1, sleep=0.1)

    if fail:
        assert is_ready is False
    else:
        assert is_ready is True


@pytest.mark.parametrize("fail", [True, False])
@pytest.mark.parametrize("fail_case", [0, 1])
def test_wait_etcd(mocker, fail, fail_case):
    class FakeEtcdClient(object):
        def __init__(self, *args, **kwargs):
            pass

        @property
        def stats(self):
            if fail:
                if fail_case == 0:
                    raise EtcdException
                else:
                    return {
                        "state": "StateLeader",
                        "leaderInfo": {
                            "leader": ""
                        }
                    }
            else:
                return {
                    "state": "StateLeader",
                    "leaderInfo": {
                        "leader": "YOLO"
                    }
                }

    mocker.patch("loktar.check.EtcdClient", return_value=FakeEtcdClient())
    is_ready = wait_etcd(retries=1, sleep=0.1)

    if fail:
        assert is_ready is False
    else:
        assert is_ready is True


@pytest.mark.parametrize("fail", [True, False])
def test_wait_mongo(mocker, fail):
    class FakeMongoClient(object):
        def __init__(self, *args, **kwargs):
            pass

        def server_info(self):
            if fail:
                raise Exception
            else:
                return {}

    mocker.patch("loktar.check.MongoClient", return_value=FakeMongoClient())

    is_ready = wait_mongo(retries=1, sleep=0.1)

    if fail:
        assert is_ready is False
    else:
        assert is_ready is True


@pytest.mark.parametrize("fail", [True, False])
def test_wait_redis(mocker, fail):

    class FakeRedisClient(object):
        def __init__(self, *args, **kwargs):
            pass

        def ping(self):
            return False if fail else True

    mocker.patch("loktar.check.redis.StrictRedis", return_value=FakeRedisClient())

    is_ready = wait_redis(retries=1, sleep=0.1)

    if fail:
        assert is_ready is False
    else:
        assert is_ready is True


@pytest.mark.parametrize("fail", [True, False])
def test_wait_sqs(mocker, fail):
    class FakeSQS(object):
        def __init__(self, *args, **kwargs):
            pass

        def get_all_queues(self):
            if fail:
                raise socket.gaierror
            else:
                return list()

    mocker.patch("loktar.check.sqs_connect_to_region", return_value=FakeSQS())

    if fail:
        assert wait_sqs() is False
    else:
        assert wait_sqs() is True


@pytest.mark.parametrize("fail", [True, False])
@pytest.mark.parametrize("client_params", [
    {"user": "foo", "password": "TooImba"},
    {"user": "foo", "key_file": "My_private_key"},
    {"user": "foo", "pkey": "dasdq6576w6dqwad3w4qd454a213sda233s"},
    {"user": "foo", "WTF_My_Custom_Param": "..."}
])
def test_wait_ssh(mocker, fail, client_params):

    class FakeSSH(object):
        def __init__(self, *args, **kwargs):
            pass

        def load_system_host_keys(self, *args, **kwargs):
            pass

        def set_missing_host_key_policy(self, *args, **kwargs):
            pass

        def connect(self, *args, **kwargs):
            if fail:
                raise paramiko.SSHException
            else:
                return True

    mocker.patch("loktar.check.paramiko.SSHClient", return_value=FakeSSH())

    if "WTF_My_Custom_Param" in client_params.keys():
        with pytest.raises(ValueError) as excinfo:
            wait_ssh(retries=1, sleep=0.1, **client_params)
            assert str(excinfo) == "Keyword Argument missing (password or key_file or pkey)"
    else:
        is_ready = wait_ssh(retries=1, sleep=0.1, **client_params)

        if fail:
            assert is_ready is False
        else:
            assert is_ready is True


@pytest.mark.parametrize("fail", [True, False])
def test_wait_s3(mocker, fail):
    class FakeS3(object):
        def __init__(self, *args, **kwargs):
            pass

        def get_all_buckets(self):
            if fail:
                raise socket.gaierror
            else:
                return list()

    mocker.patch("loktar.check.s3_connect_to_region", return_value=FakeS3())

    if fail:
        assert wait_s3() is False
    else:
        assert wait_s3() is True


@pytest.mark.parametrize("fail", [True, False])
def test_wait_rds(mocker, fail):
    class FakeRDS(object):
        def __init__(self, *args, **kwargs):
            pass

        def get_all_dbinstances(self):
            if fail:
                raise socket.gaierror
            else:
                return list()

    mocker.patch("loktar.check.rds_connect_to_region", return_value=FakeRDS())

    if fail:
        assert wait_rds() is False
    else:
        assert wait_rds() is True
