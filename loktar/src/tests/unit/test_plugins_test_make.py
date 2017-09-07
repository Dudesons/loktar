import pytest

from loktar.exceptions import CITestFail
from loktar.plugins.test.make import Make
from loktar.plugins.test.make import run


@pytest.mark.parametrize("remote", [True, False])
def test_plugins_make(mocker, remote):
    mocker.patch("loktar.plugin.exe")
    run({"artifact_name": "foobar", "artifact_root_location": "/tmp"}, remote)


@pytest.mark.parametrize("remote", [True, False])
def test_plugins_make_fail_on_command(mocker, remote):
    mocker.patch("loktar.plugin.exe", return_value=False)
    with pytest.raises(CITestFail):
        run({"artifact_name": "foobar", "artifact_root_location": "/tmp"}, remote)


def test_plugins_make_fail_on_call():
    with pytest.raises(IndexError):
        output = run()
        assert output == Make.__init__.__doc__
