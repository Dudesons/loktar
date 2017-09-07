import os
import sys

from fabric.api import local

from loktar.constants import GITHUB_INFO
from loktar.constants import SLACK
from loktar.notifications import define_job_status_on_github_commit
from loktar.notifications import send_message_to_slack


def exit_properly(exit_code,
                  commit_id=None,
                  pre_command_exit=None,
                  github_notif_url=None,
                  github_notif_message=None,
                  github_description=None,
                  slack_channels=list(),
                  slack_message=None,
                  **kwargs):
    """Exist after notifying github or/and slack

    Args:
        exit_code (int): The exit code of the previous command
        commit_id (str): The commit id to attach an event
        pre_command_exit: A command to execute before to exit
        github_notif_url (str): The url link in the github notification
        github_notif_message (str): The message in the github notification
        github_description (str): The description of the github notification
        slack_channels (list): Target channels to notify
        slack_message (str): The content of the notification on slack

    """
    if commit_id is not None:
        define_job_status_on_github_commit(commit_id,
                                           "success" if exit_code == 0 else "error",
                                           github_notif_url,
                                           context=github_notif_message if github_notif_message is not None else "CI",
                                           description=github_description,
                                           user=kwargs.get("github_user", GITHUB_INFO["login"]["user"]),
                                           password=kwargs.get("github_password", GITHUB_INFO["login"]["password"]),
                                           organization=kwargs.get("github_organization", GITHUB_INFO["organization"]),
                                           repository=kwargs.get("github_repository", GITHUB_INFO["repository"]))

    if slack_channels:
        for channel in slack_channels:
            send_message_to_slack(
                slack_message,
                channel=channel,
                token=kwargs.get("slack_token", SLACK["token"])
            )

    if pre_command_exit is not None:
        local(pre_command_exit)

    sys.exit(exit_code)
