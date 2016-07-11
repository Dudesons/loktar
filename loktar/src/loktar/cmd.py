from fabric.api import local
from fabric.api import run
from fabric.api import settings

from loktar.log import Log


def exec_command_with_retry(cmd, remote, max_retry):
    """Execute and retry a command"""
    with settings(warn_only=True):
        id_try = 0
        launch = local if remote == 0 else run
        while id_try < max_retry:
            result = launch(cmd)
            if result.succeeded:
                return True
            else:
                id_try += 1
        logger = Log()
        logger.error("The command : {0} failed after {1} retries".format(cmd, max_retry))
        return False


def exe(cmd, remote=True):
    """Execute a command

    Args:
        cmd (str): Command to execute
        remote (bool): Give the context execution remote (True) or local (False)

    Returns:
        bool: True if everything went well, False otherwise
    """
    launch = run if remote else local
    with settings(warn_only=True):
        result = launch(cmd)
        if result.failed:
            logger = Log()
            logger.error(result)
            return False
        return True
