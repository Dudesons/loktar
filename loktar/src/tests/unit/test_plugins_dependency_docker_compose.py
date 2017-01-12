import pytest

from loktar.plugins.dependency.docker_compose import docker_compose_deps


def test_docker_compose(mocker, monkeypatch):
    def fake_yaml(docker_compose_file):
        if docker_compose_file == "/toto/docker-compose.yaml":
            return {
                "services": {
                    "api": {},
                    "front": {},
                    "elasticsearch": {},
                    "worker": {}
                }
            }
        elif docker_compose_file == "/toto/docker-compose.dev.yaml":
            return {
                "services": {
                    "dynalite": {},
                    "fakes3": {}
                }
            }

    mocker.patch("loktar.plugins.dependency.docker_compose.yaml.safe_load", side_effect=fake_yaml)
    monkeypatch.setattr("os.listdir", lambda _: ["docker-compose.yaml", "docker-compose.dev.yaml"])
    assert docker_compose_deps("/toto/") == {"api", "front", "elasticsearch", "worker", "dynalite", "fakes3"}
