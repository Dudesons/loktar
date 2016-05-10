import pytest

from loktar.cmd import exe
from loktar.cmd import exec_command_with_retry


class FakeFabricFail(object):
    def __init__(self, *args, **kwargs):
        pass

    @property
    def failed(self):
        return True

    @property
    def succeeded(self):
        return False


class FakeFabricSuccess(object):
    def __init__(self, *args, **kwargs):
        pass

    @property
    def failed(self):
        return False

    @property
    def succeeded(self):
        return True


@pytest.mark.parametrize('remote', [True, False])
def test_exe(mocker, remote):
    mocker.patch("loktar.cmd.local", return_value=FakeFabricSuccess())
    mocker.patch("loktar.cmd.run", return_value=FakeFabricSuccess())

    assert exe("ls -la", remote=remote) is True


@pytest.mark.parametrize('remote', [True, False])
def test_exe_fail(mocker, remote):
    mocker.patch("loktar.cmd.local", return_value=FakeFabricFail())
    mocker.patch("loktar.cmd.run", return_value=FakeFabricFail())

    assert exe("ls -la", remote=remote) is False


@pytest.mark.parametrize('remote', [True, False])
def test_exec_with_retry(mocker, remote):
    mocker.patch("loktar.cmd.local", return_value=FakeFabricSuccess())
    mocker.patch("loktar.cmd.run", return_value=FakeFabricSuccess())

    assert exec_command_with_retry("ls -la", remote, 2) is True


@pytest.mark.parametrize('remote', [True, False])
def test_exec_with_retry_fail(mocker, remote):
    mocker.patch("loktar.cmd.local", return_value=FakeFabricFail())
    mocker.patch("loktar.cmd.run", return_value=FakeFabricFail())

    assert exec_command_with_retry("ls -la", remote, 2) is False
