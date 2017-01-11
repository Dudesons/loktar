import pytest

from loktar.exit import exit_properly


@pytest.mark.parametrize("exit_code", [0, 1])
def test_exit_properly(mocker, monkeypatch, exit_code):
    mocker.patch("loktar.exit.define_job_status_on_github_commit")
    mocker.patch("loktar.exit.local")
    monkeypatch.setenv("BUILD_URL", "http://foobar/job/5452156")
    exit_properly(exit_code, commit_id="d4sq5d4sq5d4qs54dqs5", pre_command_exit="ls /tmp")
