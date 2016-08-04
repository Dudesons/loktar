from loktar.dependency import package_from_path
from loktar.environment import GITHUB_INFO
from loktar.exceptions import PrepareEnvFail
from loktar.exceptions import SCMError
from loktar.log import Log
from loktar.scm import Github

logger = Log()


def _find_modified_files_from_github(git_branch, **kwargs):
    github = Github(kwargs.get("github_user", GITHUB_INFO['login']['user']),
                    kwargs.get("github_password", GITHUB_INFO['login']['password']),
                    github_organization=kwargs.get("github_organization", GITHUB_INFO['organization']),
                    github_repository=kwargs.get("github_repository", GITHUB_INFO['repository']))

    try:
        if git_branch == "master":
            return github.get_modified_files_from_commit(kwargs.get("commit_id"))
        else:
            return github.get_modified_files_from_pull_request(kwargs.get("pull_request_id"))
    except SCMError as e:
        logger.error(str(e))
        raise


def find_artifact_modified(git_branch, scm_type, ci_config, **kwargs):
    """Find artifact modified on a branch, PR ...

    Args:
        git_branch (str): the actual git branch
        scm_type (str): the type of scm use for finding artifact modified (eg: github, git-local ...)
        ci_config (dict): the config.json

    Returns:
        Set of artifact modified
    """
    if scm_type == "github":
        git_diff = _find_modified_files_from_github(git_branch, **kwargs)
    else:
        raise PrepareEnvFail("The scm type {} is unknown for searching artifacts".format(scm_type))

    packages_map = {pkg["pkg_name"]: pkg for pkg in ci_config['packages']}
    # generate modified packages
    return {package_from_path(path, packages_map) for path in git_diff} - {None}
