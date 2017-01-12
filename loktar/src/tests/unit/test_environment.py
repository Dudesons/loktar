import pytest

from loktar.environment import get_config
from loktar.environment import prepare_test_env
from loktar.environment import PrepareEnvFail


@pytest.mark.parametrize("full", [False, True])
def test_get_config(mocker, full):
    mocker.patch("loktar.environment.lcd")
    mocker.patch("loktar.environment.json", return_value={"packages": [{"artifact_name": "foobar"}]})
    mocker.patch("loktar.environment.local")

    get_config("foobar", "toto", full=full)


@pytest.mark.parametrize("branch", ["master", "foobar"])
def test_prepare_test_env(mocker, branch):
    mocker.patch("loktar.environment.os")
    mocker.patch("loktar.environment.lcd")
    mocker.patch("loktar.environment.local")
    mocker.patch("loktar.environment.exec_command_with_retry")
    prepare_test_env(branch)


@pytest.mark.parametrize("branch", ["master", "foobar"])
@pytest.mark.parametrize("when_to_fail", [
    "git clone -b ",
    "git fetch origin master",
    "git config --global user.email 'you@example.com'",
    "git config --global user.name 'Your Name'",
    "git merge --no-ff --no-edit FETCH_HEAD",
    "tar -czf "
])
def test_prepare_test_env_prepare_env_fail(mocker, branch, when_to_fail):

    def fake_exec_command_with_retry(cmd, *args, **kwargs):
        if when_to_fail in cmd:
            return False

    mocker.patch("loktar.environment.os")
    mocker.patch("loktar.environment.lcd")
    mocker.patch("loktar.environment.local")
    mocker.patch("loktar.environment.exec_command_with_retry", side_effect=fake_exec_command_with_retry)
    with pytest.raises(PrepareEnvFail):
        prepare_test_env(branch)
