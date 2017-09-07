import pytest

from loktar.plugins.dependency.docker_compose import docker_compose_deps


def test_docker_compose(mocker, monkeypatch):
    class FakeFile(object):
        def __init__(self):
            pass

        def read(self, *args, **kwargs):
            return 'version: "2"\n\nservices:\n  redis:\n    image: redis\n\n  elasticsearch:\n    image: elasticsearch:5.0\n\n\n  api:\n    image: api\n\n  worker:\n    image: worker:3.3\n\n  front:\n    build: .\n'

        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

        def __enter__(self):
            return self

    def fake_open(*args, **kwargs):
        return FakeFile()

    mocker.patch("__builtin__.open", return_value=fake_open())
    monkeypatch.setattr("os.listdir", lambda _: ["docker-compose.yaml", "docker-compose.dev.yaml"])
    assert docker_compose_deps("/toto/") == {"api", "front", "elasticsearch", "worker", "redis"}
