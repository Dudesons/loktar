# from mockredis import mock_strict_redis_client
from conftest import FakeElasticSearch
import pytest

from loktar.db import Run


# from loktar.db import redis


@pytest.fixture()
def mock_env(mocker):
    return mocker.patch("loktar.db.RUN_DB",
                        return_value={
                            "host": "foo",
                            "port": "bar",
                            "db": "toto",
                            "table": "plop"
                        })


def test_define_job_status_on_github_commit(mocker, mock_env):
    mocker.patch("loktar.db.Elasticsearch", return_value=FakeElasticSearch())

    results = list()
    run = Run()
    results.append(run.set_run({"foo": "bar0", "awesome": "payload0"}))
    results.append(run.set_run({"foo": "bar1", "awesome": "payload1"}))
    results.append(run.set_run({"foo": "bar2", "awesome": "payload2"}))

    for i in xrange(len(results)):
        assert run.get_run(results[i]) == {"foo": "bar{}".format(i), "awesome": "payload{}".format(i)}

    assert run.get_runs() == [{'awesome': 'payload0', 'foo': 'bar0'},
                              {'awesome': 'payload1', 'foo': 'bar1'},
                              {'awesome': 'payload2', 'foo': 'bar2'}]
