import pytest

from loktar.container import start_container
from loktar.container import clean_container


class FakeContainer(object):
    def __init__(self, *args, **kwargs):
        self.attrs = {
            "NetworkSettings": {
                "Ports": {
                    "net0": [{"HostPort": 2222}, {}]

                }
            },
            "Node": {
                "IP": "127.0.0.1"
            }
        }
        self.id = "qwertyuiop"

    def kill(self):
        pass

    def remove(self):
        pass

    def start(self):
        pass


class FakeSubCommand(object):
    def __init__(self):
        pass

    @property
    def run(self, *args, **kwargs):
        return FakeContainer

    @property
    def get(self, *args, **kwargs):
        return FakeContainer


class FakeClient(object):
    def __init__(self):
        self.containers = FakeSubCommand()

    def login(self, *args, **kwargs):
        return True


def fake_docker_client():
    return FakeClient()


def test_start_container(mocker):
    mocker.patch("loktar.container.DockerClient", return_value=fake_docker_client())
    container_info = start_container("foo/bar:1", {"MY_ENV": "KILLER_ENV"}, {"22/tcp": None})

    assert container_info["host"] == "127.0.0.1"
    assert container_info["host_port"] == 2222
    assert container_info["id"] == "qwertyuiop"


def test_clean_container(mocker):
    mocker.patch("loktar.container.DockerClient", return_value=fake_docker_client())
    clean_container("qwpeowqpasdalsdpasd")
