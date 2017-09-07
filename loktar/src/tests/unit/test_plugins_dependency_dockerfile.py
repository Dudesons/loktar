import pytest

from loktar.plugins.dependency.dockerfile import docker_deps


def test_docker_deps(mocker, monkeypatch):
    class FakeFile(object):
        def __init__(self, *Args, **kwargs):
            pass

        def read(self):
            return "FROM my_awesome_base_image:42\nRUN sleep 1800000000"

        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

        def __enter__(self):
            return self

    def fake_open(*args, **kwargs):
        return FakeFile()

    mocker.patch("__builtin__.open", return_value=fake_open())
    monkeypatch.setattr("os.path.exists", lambda _: True)
    assert docker_deps("/toto/") == {"my_awesome_base_image"}


def test_docker_deps_empty(mocker, monkeypatch):
    class FakeFile(object):
        def __init__(self, *Args, **kwargs):
            pass

        def read(self):
            return ""

        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

        def __enter__(self):
            return self

    def fake_open(*args, **kwargs):
        return FakeFile()

    mocker.patch("__builtin__.open", return_value=fake_open())
    monkeypatch.setattr("os.path.exists", lambda _: True)
    assert docker_deps("/toto/") == set()


def test_docker_deps_file_absent(monkeypatch):
    monkeypatch.setattr("os.path.exists", lambda _: False)
    assert docker_deps("/toto/") == set()
