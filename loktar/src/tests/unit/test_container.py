import pytest

from loktar.container import start_container
from loktar.container import clean_container
from loktar.exceptions import CIJobFail


def test_start_container(mocker, fake_docker_client):
    mocker.patch("loktar.container.DockerClient", return_value=fake_docker_client())
    container_info = start_container("foo/bar:1", {"MY_ENV": "KILLER_ENV"}, {"22/tcp": None})

    assert container_info["host"] == "127.0.0.1"
    assert container_info["host_port"] == 2222
    assert container_info["id"] == "qwertyuiop"


def test_fail_start_container(mocker, fake_docker_client):
    mocker.patch("loktar.container.DockerClient", return_value=fake_docker_client(container_status="dead"))
    with pytest.raises(CIJobFail) as e:
        start_container("foo/bar:1", {"MY_ENV": "KILLER_ENV"}, {"22/tcp": None})
        assert str(e) == "CIJobFail: CIJobFail: Fail to contact the container"


def test_clean_container(mocker, fake_docker_client):
    mocker.patch("loktar.container.DockerClient", return_value=fake_docker_client())
    clean_container("qwpeowqpasdalsdpasd")
