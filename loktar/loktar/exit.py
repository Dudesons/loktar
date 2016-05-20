import os
import sys

from fabric.api import local

from loktar.notifications import define_job_status_on_github_commit


def exit_properly(exit_code,
                  commit_id=None,
                  pre_command_exit=None,
                  notif_msg=None,
                  description=None):
    """Exist after notifying github

    Args:
        exit_code:
        commit_id:
        pre_command_exit:
        notif_msg:
        description:

    """
    if commit_id is not None:
        define_job_status_on_github_commit(commit_id,
                                           'success' if exit_code == 0 else 'error',
                                           os.environ.get('BUILD_URL') + 'console#footer-container',
                                           context=notif_msg if notif_msg is not None else 'CI',
                                           description=description)
    if pre_command_exit is not None:
        local(pre_command_exit)

    sys.exit(exit_code)
