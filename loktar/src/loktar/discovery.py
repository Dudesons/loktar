from loktar.constants import GITHUB_INFO
from loktar.cmd import cwd
from loktar.cmd import exe
from loktar.dependency import artifact_from_path
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
            dict_message_files = github.get_commit_message_modified_files_on_pull_request(kwargs.get("pull_request_id"))
            # Filter out Merge remote-tracking commits and Merge branch
            dict_message_files = {key: value for key, value in dict_message_files.iteritems()
                                  if (not key.startswith('Merge remote-tracking branch') and
                                      not key.startswith('Merge branch'))}

            # This is the git diff, concatenate the lists that are values of dict_message_files
            return [item for _list in dict_message_files.values() for item in _list]
    except SCMError as e:
        logger.error(str(e))
        raise


def _find_modified_files_from_local_git(git_branch, **kwargs):
    with cwd(kwargs.get("workspace"), remote=kwargs.get("remote")):
        exe("git checkout {}".format(git_branch), remote=kwargs.get("remote"))
        git_diff = exe("git diff HEAD~ HEAD --name-only", remote=kwargs.get("remote"))
        return filter(None, list(set(git_diff.split("\n"))))


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
    elif scm_type == "git":
        git_diff = _find_modified_files_from_local_git(git_branch, **kwargs)
    else:
        raise PrepareEnvFail("The scm type {} is unknown for searching artifacts".format(scm_type))

    packages_map = {pkg["artifact_name"]: pkg for pkg in ci_config['packages']}
    # generate modified packages
    return {artifact_from_path(path, packages_map) for path in git_diff} - {None}
