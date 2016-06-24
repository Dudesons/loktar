import pytest

from loktar.exceptions import CIBuildPackageFail
from loktar.plugins.whl import PypicloudClient
from loktar.plugins.whl import run
from loktar.plugins.whl import Whl


@pytest.fixture()
def os_environ(mocker):
    environ = dict(
        PYPICLOUD_HOST="host",
        PYPICLOUD_USER="root",
        PYPICLOUD_PASSWORD="toor"
    )
    mocker.patch.dict("os.environ", environ)
    return environ


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


def test_plugins_whl_fail_on_call():
    with pytest.raises(IndexError):
        output = run()
        assert output == Whl.__init__.__doc__


@pytest.mark.parametrize("mode", ["master", "foo_bar"])
@pytest.mark.parametrize("pypicloud_get_versions", [
    (
            {
                "name": "flywheel",
                "last_modified": 1389945600,
                "version": "1",
                "url": "https://pypi.s3.amazonaws.com/34c2/",
                "filename": "flywheel-1.tar.gz"
            },
            {
                "name": "flywheel",
                "last_modified": 1389945600,
                "version": "2",
                "url": "https://pypi.s3.amazonaws.com/34c2/",
                "filename": "flywheel-2.tar.gz"
            },
            {
                "name": "flywheel",
                "last_modified": 1389945600,
                "version": "3",
                "url": "https://pypi.s3.amazonaws.com/34c2/",
                "filename": "flywheel-3.tar.gz"
            },
            {
                "name": "flywheel",
                "last_modified": 1389945600,
                "version": "4",
                "url": "https://pypi.s3.amazonaws.com/34c2/",
                "filename": "flywheel-4.tar.gz"
            },
            {
                "name": "flywheel",
                "last_modified": 1390207478,
                "version": "0.foo-bar",
                "url": "https://pypi.s3.amazonaws.com/81f2/flywheel-0.1.0-21-g4a739b0.tar.gz",
                "filename": "flywheel-0.1.0-21-g4a739b0.tar.gz"
            }
    ),
    (
            {
                "name": "flywheel",
                "last_modified": 1389945600,
                "version": "9",
                "url": "https://pypi.s3.amazonaws.com/34c2/",
                "filename": "flywheel-9.tar.gz"
            },
            {
                "name": "flywheel",
                "last_modified": 1389945600,
                "version": "10",
                "url": "https://pypi.s3.amazonaws.com/34c2/",
                "filename": "flywheel-10.tar.gz"
            },
            {
                "name": "flywheel",
                "last_modified": 1389945600,
                "version": "11",
                "url": "https://pypi.s3.amazonaws.com/34c2/",
                "filename": "flywheel-11.tar.gz"
            },
    ),
    (
            {
                "name": "flywheel",
                "last_modified": 1389945600,
                "version": "0.foobar-bar",
                "url": "https://pypi.s3.amazonaws.com/34c2/",
                "filename": "flywheel-0-foobar-bar.tar.gz"
            },
    )
])
def test_plugins_whl_get_next_version(monkeypatch, mode, pypicloud_get_versions, os_environ):
    monkeypatch.setattr(PypicloudClient, "get_versions", lambda *args: pypicloud_get_versions)

    plugin = Whl(
        {
            "pkg_name": "foobar",
            "test_type": "make",
            "type": "library",
            "pkg_type": "whl",
            "package_location": "/tmp/490847a2-326c-41c6-abb6-5765fc7544b3",
            "mode": mode
            
        },
        False
    )

    if mode == "master":
        if len(pypicloud_get_versions) == 1:
            expected_value = "1"
        elif len(pypicloud_get_versions) == 3:
            expected_value = "12"
        else:
            expected_value = "5"
    else:
        expected_value = "0.foo-bar"

    plugin.get_next_version()

    assert str(plugin.share_memory["latest_version"]) == expected_value
