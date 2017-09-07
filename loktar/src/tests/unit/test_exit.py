from flexmock import flexmock
import pytest

from loktar import exit


@pytest.mark.parametrize("exit_code", [0, 1])
def test_exit_properly(mocker, monkeypatch, exit_code):
    commit_id = "c0mm1tID"
    pre_command_exit = "rm -rf /tmp"
    github_notif_url = "http://ci_marche_pas.io/grossec-test/12/console#footer"
    github_notif_message = "That build"
    github_description = "..."
    slack_channels = ["PythonPowa", "Plop"]
    slack_message = "Hello everyone"
    slack_token = "MyAwesomeTokenSlack"
    github_user = "foobar"
    github_password = "beimba"
    github_organization = "qwerty"
    github_repository = "azerty"

    flexmock(exit) \
        .should_receive("define_job_status_on_github_commit") \
        .with_args(commit_id,
                   "success" if exit_code == 0 else "error",
                   github_notif_url,
                   context=github_notif_message,
                   description=github_description,
                   user=github_user,
                   password=github_password,
                   organization=github_organization,
                   repository=github_repository) \
        .and_return(None)

    flexmock(exit) \
        .should_receive("send_message_to_slack") \
        .with_args(slack_message,
                   channel=slack_channels[0],
                   token="MyAwesomeTokenSlack") \
        .and_return(None) \
        .ordered()

    flexmock(exit) \
        .should_receive("send_message_to_slack") \
        .with_args(slack_message,
                   channel=slack_channels[1],
                   token=slack_token) \
        .and_return(None) \
        .ordered()

    flexmock(exit) \
        .should_receive("local") \
        .with_args(pre_command_exit) \
        .and_return(None) \
        .ordered()

    exit.exit_properly(exit_code,
                       commit_id=commit_id,
                       pre_command_exit=pre_command_exit,
                       github_notif_url=github_notif_url,
                       github_notif_message=github_notif_message,
                       github_description=github_description,
                       github_user=github_user,
                       github_password=github_password,
                       github_organization=github_organization,
                       github_repository=github_repository,
                       slack_channels=slack_channels,
                       slack_message=slack_message,
                       slack_token=slack_token)


@pytest.mark.parametrize("exit_code", [0, 1])
def test_exit_properly_fallback_environment(mocker, monkeypatch, exit_code):
    commit_id = "c0mm1tID"
    pre_command_exit = "rm -rf /tmp"
    github_notif_url = "http://ci_marche_pas.io/grossec-test/12/console#footer"
    github_notif_message = "That build"
    github_description = "..."
    slack_channels = ["PythonPowa", "Plop"]
    slack_message = "Hello everyone"
    slack_token = "MyAwesomeTokenSlack_in_env"
    github_user = "foobar_in_env"
    github_password = "beimba_in_env"
    github_organization = "qwerty_in_env"
    github_repository = "azerty_in_env"

    flexmock(exit) \
        .should_receive("SLACK") \
        .and_return({
            "token": slack_token
        })

    flexmock(exit) \
        .should_receive("GITHUB_INFO") \
        .and_return({
            "login": {
                "user": github_user,
                "password": github_password,
            },
            "organization": github_organization,
            "repository": github_repository,
        })

    flexmock(exit) \
        .should_receive("define_job_status_on_github_commit") \
        .with_args(commit_id,
                   "success" if exit_code == 0 else "error",
                   github_notif_url,
                   context=github_notif_message,
                   description=github_description,
                   user=github_user,
                   password=github_password,
                   organization=github_organization,
                   repository=github_repository) \
        .and_return(None)

    flexmock(exit) \
        .should_receive("send_message_to_slack") \
        .with_args(slack_message,
                   channel=slack_channels[0],
                   token=slack_token) \
        .and_return(None) \
        .ordered()

    flexmock(exit) \
        .should_receive("send_message_to_slack") \
        .with_args(slack_message,
                   channel=slack_channels[1],
                   token=slack_token) \
        .and_return(None) \
        .ordered()

    flexmock(exit) \
        .should_receive("local") \
        .with_args(pre_command_exit) \
        .and_return(None) \
        .ordered()

    exit.exit_properly(exit_code,
                       commit_id=commit_id,
                       pre_command_exit=pre_command_exit,
                       github_notif_url=github_notif_url,
                       github_notif_message=github_notif_message,
                       github_description=github_description,
                       slack_channels=slack_channels,
                       slack_message=slack_message)
