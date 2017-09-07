import pytest

from loktar.exceptions import CIBuildPackageFail
from loktar.exceptions import CITestFail
from loktar.plugins.artifact.emr import EMR
from loktar.plugins.artifact.emr import run


@pytest.fixture()
def ci_payload():
    payload = {
        "artifact_name": "foobar",
        "artifact_root_location": "/tmp",
        "artifact_type": "emr",
        "build_info": {
            "input_type": "jar",
            "bucket_name": "foo-emr",
            "prefix_command": "docker-compose run bar"
        }
    }
    return payload


@pytest.mark.parametrize("remote", [True, False])
@pytest.mark.parametrize("mode", ["master", "foobranch"])
def test_plugins_emr(mocker, remote, ci_payload, mode):
    mocker.patch("loktar.plugin.exe")

    ci_payload["mode"] = mode

    run(ci_payload, remote)


@pytest.mark.parametrize("remote", [True, False])
@pytest.mark.parametrize("mode", ["master", "foobranch"])
def test_plugins_emr_fail_on_command(mocker, remote, ci_payload, mode):
    mocker.patch("loktar.plugin.exe", return_value=False)

    ci_payload["mode"] = mode

    with pytest.raises(CITestFail):
        run(ci_payload, remote)


def test_plugins_emr_fail_on_call():
    with pytest.raises(TypeError):
        output = run()
        assert output == EMR.__init__.__doc__


@pytest.mark.parametrize("remote", [True, False])
def test_plugins_emr_fail_on_input_type(mocker, remote, ci_payload):
    mocker.patch("loktar.plugin.exe")

    input_type = "the new and awesome input type"
    ci_payload["build_info"]["input_type"] = input_type

    with pytest.raises(CIBuildPackageFail) as excinfo:
        run(ci_payload, remote)
        assert str(excinfo) == "the input type : '{}' is not managed, create a pr for integrate this input type"\
                               .format(input_type)
