import pytest

from loktar.exceptions import CITestFail
from loktar.plugins.make import run


def test_plugins_make(mocker):
    mocker.patch("loktar.plugin.exe")
    run({"pkg_name": "foobar", "package_location": "/tmp"})


def test_plugins_make_fail_on_update_version(mocker):
    mocker.patch("loktar.plugin.exe", return_value=False)
    with pytest.raises(CITestFail):
        run({"pkg_name": "foobar", "package_location": "/tmp"})
