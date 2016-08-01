import pytest

from loktar.exceptions import CITestFail
from loktar.plugins.artifact.emr import EMR
from loktar.plugins.artifact.emr import run


@pytest.fixture()
def ci_payload():
    payload = {
        "pkg_name": "foobar",
        "package_location": "/tmp",
        "pkg_type": "emr",
        "build_info": {
            "input_type": "jar",
            "bucket_name": "foo-emr",
            "prefix_command": "docker-compose run bar"
        }
    }
    return payload


@pytest.mark.parametrize("remote", [True, False])
@pytest.mark.parametrize("mode", ["master", "foobranch"])
def test_plugins_make(mocker, remote, ci_payload, mode):
    mocker.patch("loktar.plugin.exe")

    ci_payload["mode"] = mode

    run(ci_payload, remote)


@pytest.mark.parametrize("remote", [True, False])
@pytest.mark.parametrize("mode", ["master", "foobranch"])
def test_plugins_make_fail_on_command(mocker, remote, ci_payload, mode):
    mocker.patch("loktar.plugin.exe", return_value=False)

    ci_payload["mode"] = mode

    with pytest.raises(CITestFail):
        run(ci_payload, remote)


def test_plugins_make_fail_on_call():
    with pytest.raises(TypeError):
        output = run()
        assert output == EMR.__init__.__doc__
