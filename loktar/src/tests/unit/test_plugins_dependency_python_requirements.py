import pytest

from loktar.plugins.dependency.python_requirements import python_deps


def test_python_deps(mocker, monkeypatch):
    class FakeFile(object):
        def __init__(self, *args, **kwargs):
            pass

        def readlines(self):
            return [
                "q==0",
                "w>=1",
                "e>2",
                "r<=3",
                "t<4",
                "y"
            ]

        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

        def __enter__(self):
            return self

    def fake_open(*args, **kwargs):
        return FakeFile()

    mocker.patch("__builtin__.open", return_value=fake_open())
    monkeypatch.setattr("os.path.exists", lambda _: True)
    assert python_deps("/toto/") == {"q", "w", "e", "r", "t", "y"}


def test_python_deps_empty(mocker, monkeypatch):
    class FakeFile(object):
        def __init__(self, *Args, **kwargs):
            pass

        def readlines(self):
            return []

        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

        def __enter__(self):
            return self

    def fake_open(*args, **kwargs):
        return FakeFile()

    mocker.patch("__builtin__.open", return_value=fake_open())
    monkeypatch.setattr("os.path.exists", lambda _: True)
    assert python_deps("/toto/") == set()


def test_python_deps_file_absent(mocker, monkeypatch):
    monkeypatch.setattr("os.path.exists", lambda _: False)
    assert python_deps("/toto/") == set()
