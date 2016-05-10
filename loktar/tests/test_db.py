from mockredis import mock_strict_redis_client
import pytest


from loktar.db import redis
from loktar.db import Job


def test_define_job_status_on_github_commit(monkeypatch):
    def mock_return(*args, **kwargs):
        return mock_strict_redis_client()

    monkeypatch.setattr(redis, 'StrictRedis', mock_return)

    job = Job()
    assert job.set_job("1d5q1d5", {"foo": "bar0", "awesome": "payload0"}) is True
    assert job.set_job("1dqs52d", {"foo": "bar1", "awesome": "payload1"}) is True
    assert job.set_job("8d78s44", {"foo": "bar2", "awesome": "payload2"}) is True
    assert job.get_job("1d5q1d5") == {"foo": "bar0", "awesome": "payload0"}
    assert job.get_jobs() == [{'awesome': 'payload0', 'foo': 'bar0'}, {'awesome': 'payload1', 'foo': 'bar1'}, {'awesome': 'payload2', 'foo': 'bar2'}]
