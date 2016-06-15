import pytest

from loktar.exceptions import CITestFail
from loktar.plugins.make import run


@pytest.mark.parametrize("remote", [True, False])
def test_plugins_make(mocker, remote):
    mocker.patch("loktar.plugin.exe")
    run({"pkg_name": "foobar", "package_location": "/tmp"}, remote)


@pytest.mark.parametrize("remote", [True, False])
def test_plugins_make_fail_on_update_version(mocker, remote):
    mocker.patch("loktar.plugin.exe", return_value=False)
    with pytest.raises(CITestFail):
        run({"pkg_name": "foobar", "package_location": "/tmp"}, remote)
