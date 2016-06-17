import pytest

from loktar.exceptions import CIBuildPackageFail
from loktar.plugins.whl import run


@pytest.mark.parametrize("mode", ["master", "foobar"])
@pytest.mark.parametrize("remote", [True, False])
def test_plugins_whl(mocker, mode, remote):
    mocker.patch("loktar.plugins.whl.PypicloudClient")
    mocker.patch("loktar.plugins.whl.exe")
    mocker.patch("loktar.plugins.whl.exec_command_with_retry")
    mocker.patch("loktar.plugin.exe")
    run({"pkg_name": "foobar", "mode": mode, "package_location": "/tmp"}, remote)


@pytest.mark.parametrize("mode", ["master", "foobar"])
@pytest.mark.parametrize("remote", [True, False])
def test_plugins_whl_fail_on_update_version(mocker, mode, remote):
    mocker.patch("loktar.plugins.whl.PypicloudClient")
    mocker.patch("loktar.plugins.whl.exe", return_value=False)
    mocker.patch("loktar.plugins.whl.exec_command_with_retry")
    mocker.patch("loktar.plugin.exe")
    with pytest.raises(CIBuildPackageFail):
        run({"pkg_name": "foobar", "mode": mode, "package_location": "/tmp"}, remote)


@pytest.mark.parametrize("mode", ["master", "foobar"])
@pytest.mark.parametrize("remote", [True, False])
def test_plugins_whl_fail_on_release(mocker, mode, remote):
    mocker.patch("loktar.plugins.whl.PypicloudClient")
    mocker.patch("loktar.plugins.whl.exe")
    mocker.patch("loktar.plugins.whl.exec_command_with_retry", return_value=False)
    mocker.patch("loktar.plugin.exe")
    with pytest.raises(CIBuildPackageFail):
        run({"pkg_name": "foobar", "mode": mode, "package_location": "/tmp"}, remote)
