import pytest

from loktar.exceptions import CIBuildPackageFail
from loktar.plugins.artifact.jvm import _Maven
from loktar.plugins.artifact.jvm import JVM
from loktar.plugins.artifact.jvm import run


@pytest.fixture()
def ci_payload():
    payload = {
        "artifact_name": "foobar",
        "artifact_root_location": "/tmp",
        "artifact_type": "jvm",
        "build_info": {
            "build_type": "sbt",
            "prefix_command": "docker-compose run bar"
        }
    }
    return payload


@pytest.mark.parametrize("remote", [True, False])
@pytest.mark.parametrize("mode", ["master", "foobranch"])
@pytest.mark.parametrize("build_type", ["sbt", "maven"])
def test_plugins_jvm(mocker, remote, ci_payload, mode, build_type):
    mocker.patch("loktar.plugin.exe")
    mocker.patch("loktar.plugins.artifact.jvm.exec_with_output_capture",
                 return_value=(True, "build.sbt\nnoob.scala\npython_is_better_than.scala"))

    ci_payload["mode"] = mode
    ci_payload["build_info"]["build_type"] = build_type

    run(ci_payload, remote)


@pytest.mark.parametrize("remote", [True, False])
@pytest.mark.parametrize("mode", ["master", "foobranch"])
def test_plugins_jvm_fail_on_command(mocker, remote, ci_payload, mode):
    mocker.patch("loktar.plugin.exe", return_value=False)
    mocker.patch("loktar.plugins.artifact.jvm.exec_with_output_capture",
                 return_value=(False, "build.sbt\nnoob.scala\npython_is_better_than.scala"))

    ci_payload["mode"] = mode

    with pytest.raises(OSError):
        run(ci_payload, remote)


def test_plugins_jvm_fail_on_call():
    with pytest.raises(TypeError):
        output = run()
        assert output == JVM.__init__.__doc__


@pytest.mark.parametrize("remote", [True, False])
def test_plugins_jvm_fail_on_input_type(mocker, remote, ci_payload):
    mocker.patch("loktar.plugin.exe")
    mocker.patch("loktar.plugins.artifact.jvm.exec_with_output_capture",
                 return_value=(True, "build.sbt\nnoob.scala\npython_is_better_than.scala"))

    input_type = "the new and awesome input type"
    ci_payload["build_info"]["build_type"] = input_type
    with pytest.raises(CIBuildPackageFail) as excinfo:
        run(ci_payload, remote)
        assert str(excinfo) == "the input type : '{}' is not managed, create a pr for integrate this input type"\
                               .format(input_type)


@pytest.mark.parametrize("remote", [True, False])
@pytest.mark.parametrize("mode", ["master", "foobranch"])
def test_plugins_maven_commands(ci_payload, remote, mode):
    ci_payload["mode"] = mode

    mvn = _Maven(ci_payload, remote)

    if mode == "master":
        assert mvn.config["command"]["run"] == "docker-compose run bar mvn -Darguments=\"-DskipTests\" --batch-mode release:prepare release:perform"
    else:
        assert mvn.config["command"]["run"] == "docker-compose run bar mvn deploy"
