from mock import MagicMock
import pytest
from fabric.api import local

from loktar.cmd import cwd
from loktar.cmd import exe
from loktar.cmd import exec_command_with_retry
from loktar.cmd import exec_with_output_capture
from loktar.cmd import transfer_file


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

    def split(self, _):
        return ["q", "w", "e"]


class FakeFabric(object):
    def __init__(self, rc, *args, **kwargs):
        self.rc = rc

    @property
    def failed(self):
        return self.rc

    @property
    def succeeded(self):
        return self.rc

    def split(self, _):
        return ["q", "w", "e"]


@pytest.fixture
def fake_fabric():
    return FakeFabric

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
@pytest.mark.parametrize('force_return_code', [True, False])
def test_exe_force_return_code(mocker, fake_fabric, remote, force_return_code):
    fabric_object = fake_fabric(force_return_code)
    mocker.patch("loktar.cmd.local", return_value=fabric_object)
    mocker.patch("loktar.cmd.run", return_value=fabric_object)

    assert exe("ls -la", remote=remote, force_return_code=force_return_code) is force_return_code


@pytest.mark.parametrize('remote', [True, False])
def test_exec_with_retry(mocker, remote):
    mocker.patch("loktar.cmd.local", return_value=FakeFabricSuccess())
    mocker.patch("loktar.cmd.run", return_value=FakeFabricSuccess())

    assert exec_command_with_retry("ls -la", remote, 2) is True


@pytest.mark.parametrize('remote', [True, False])
@pytest.mark.parametrize('force_return_code', [True, False])
def test_exec_with_retry_force_return_code(mocker, fake_fabric, remote, force_return_code):
    fabric_object = fake_fabric(force_return_code)
    mocker.patch("loktar.cmd.local", return_value=fabric_object)
    mocker.patch("loktar.cmd.run", return_value=fabric_object)

    assert exec_command_with_retry("ls -la", remote, 2, force_return_code=force_return_code) is force_return_code


@pytest.mark.parametrize('remote', [True, False])
def test_exec_with_retry_fail(mocker, remote):
    mocker.patch("loktar.cmd.local", return_value=FakeFabricFail())
    mocker.patch("loktar.cmd.run", return_value=FakeFabricFail())

    assert exec_command_with_retry("ls -la", remote, 2) is False


@pytest.mark.parametrize('r_failed', [True, False])
@pytest.mark.parametrize('action', ['GET', 'PUSH', 'other'])
def test_transfer_file(mocker, r_failed, action):
    response = MagicMock(failed=r_failed)
    mocker.patch("loktar.cmd.get", return_value=response)
    mocker.patch("loktar.cmd.put", return_value=response)

    assert transfer_file(action, 'remote_path', 'local_path') != r_failed or action == 'other'
    assert not transfer_file(action)


def test_cwd():
    with cwd("/tmp", remote=False):
        path = local("pwd", capture=True)
        assert path == "/tmp"


@pytest.mark.parametrize('remote', [True, False])
def test_exec_with_output_capture(mocker, remote):
    mocker.patch("loktar.cmd.local", return_value=FakeFabricSuccess())
    mocker.patch("loktar.cmd.run", return_value=FakeFabricSuccess())
    exec_with_output_capture("ls /tmp", remote=remote)


@pytest.mark.parametrize('force_return_code', [True, False])
@pytest.mark.parametrize('remote', [True, False])
def test_exec_with_output_capture_force_return_code(mocker, fake_fabric, remote, force_return_code):
    fabric_object = fake_fabric(force_return_code)

    mocker.patch("loktar.cmd.local", return_value=fabric_object)
    mocker.patch("loktar.cmd.run", return_value=fabric_object)

    exec_with_output_capture("ls /tmp", remote=remote)
