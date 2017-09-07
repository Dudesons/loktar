from fabric.api import cd
from fabric.api import local
from fabric.api import lcd
from fabric.api import get
from fabric.api import put
from fabric.api import run
from fabric.api import settings

from loktar.log import Log

logger = Log()


def exec_command_with_retry(cmd, remote, max_retry, force_return_code=None):
    """Execute and retry a command
    Args:
        cmd (str): Command to execute
        remote (bool): Give the context execution remote (True) or local (False)
        max_retry (int): THe number or command to execute before returning error
        force_return_code (bool): Force the return code, ignoring if the command is success or failure
    """
    with settings(warn_only=True):
        id_try = 0
        launch = local if remote == 0 else run
        while id_try < max_retry:
            result = launch(cmd)
            if result.succeeded:
                return True if force_return_code is None else force_return_code
            else:
                id_try += 1

        logger.error("The command : {0} failed after {1} retries".format(cmd, max_retry))
        return False if force_return_code is None else force_return_code


def exe(cmd, remote=True, force_return_code=None):
    """Execute a command

    Args:
        cmd (str): Command to execute
        remote (bool): Give the context execution remote (True) or local (False)
        force_return_code (bool): Force the return code, ignoring if the command is success or failure

    Returns:
        bool: True if everything went well, False otherwise
    """
    launch = run if remote else local
    with settings(warn_only=True):
        result = launch(cmd)
        if result.failed:
            logger.error(result)
            return False if force_return_code is None else force_return_code
        return True if force_return_code is None else force_return_code


def exec_with_output_capture(cmd, remote=True, force_return_code=None):
    """Execute a command and capture the output

    Args:
        cmd (str): Command to execute
        remote (bool): Give the context execution remote (True) or local (False)
        force_return_code (bool): Force the return code, ignoring if the command is success or failure

    Returns:
        bool: True if everything went well, False otherwise
        result (list): The output of the command
    """
    if remote:
        launch = run
        kwargs = {}
    else:
        launch = local
        kwargs = {"capture": True}

    with settings(warn_only=True):
        result = launch(cmd, **kwargs)
        if result.failed:
            logger.error(result)
            return False if force_return_code is None else force_return_code, filter(None, result.split("\n"))
        return True if force_return_code is None else force_return_code, filter(None, result.split("\n"))


def cwd(path, remote=True):
    mv = lcd if remote is False else cd
    return mv(path)


def transfer_file(action, remote_path=None, local_path=None):
    if remote_path is not None and local_path is not None:
        if action == "GET":
            rc = get(remote_path, local_path)
        elif action == "PUSH":
            try:
                rc = put(local_path, remote_path)
            except ValueError:
                logger.error("Maybe a test in another job failed, so the tar was deleted or a network problem.")
        else:
            logger.info("Action : {0} unknown".format(action))
            return False
    else:
        logger.error("remote_path and local_path have to be set")
        return False

    if rc.failed:
        logger.error(rc)
        return False

    logger.info("File transfile is finished")
    return True
