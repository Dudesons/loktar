import copy
from fabric.api import hide
from fabric.api import lcd
from fabric.api import local
import json
import os
import time
import traceback
from uuid import uuid4
import yaml

from loktar.cmd import exec_command_with_retry
from loktar.db import Job
from loktar.dependency import dependency_graph_from_modified_packages
from loktar.dependency import gen_dependencies_level
from loktar.dependency import get_excluded_deps
from loktar.dependency import get_do_not_touch_packages
from loktar.dependency import package_from_path
from loktar.dependency import pull_request_information
from loktar.environment import GITHUB_INFO
from loktar.environment import GITHUB_TOKEN
from loktar.environment import MAX_RETRY_GITHUB
from loktar.exceptions import JobIdUnknown
from loktar.exceptions import PrepareEnvFail
from loktar.exceptions import PullRequestCollision
from loktar.job import build_params_to_context
from loktar.log import Log
from loktar.notifications import define_job_status_on_github_commit
from loktar.serialize import serialize
from loktar.scm import fetch_github_file
from loktar.scm import Github


def worker(logger=os.environ.get("LOGGER", None), rebuild=os.environ.get("REBUILD", False)):
    db = Job()
    job_id = os.environ.get("JOB_ID", None)
    detect_pr_collision = os.environ.get("JOB_ID", False)

    if job_id is None:
        raise JobIdUnknown

    job = db.get_job(job_id)
    commit_id = job["commit_id"]
    committer = job["committer"]

    job["lastAccess"] = time.time()
    job["status"] = 10

    db.set_job(job_id, job)

    if logger is not None:
        logger_info = logger.info
        logger_error = logger.error
    else:
        log = Log()
        logger_info = log.info
        logger_error = log.error


    #define_job_status_on_github_commit()

    with hide('output', 'running', 'warnings'):
        # TODO(Re-implement the line workspace = prepare_test_env(job["git_branch"]) && os.remove("{0}.tar".format(workspace)))
        # workspace = prepare_test_env(job["git_branch"])
        # TODO(Implement the file transfer to the CI server)
        # transfer_file("PUT", remote_path="/tmp", local_path="{0}.tar".format(workspace))
        # os.remove("{0}.tar".format(workspace))
        logger_info('Preparing the test environment')
        unique_name_dir = str(uuid4())
        workspace = '/mnt/ci/{0}'.format(unique_name_dir)
        os.makedirs(workspace)
        try:
            if not exec_command_with_retry('git clone git@github.com:{0}/{1}.git {2}'
                                           .format(GITHUB_INFO["organization"], GITHUB_INFO["repository"], workspace),
                                           0, MAX_RETRY_GITHUB):
                raise PrepareEnvFail
        except PrepareEnvFail:
            local('rm -rf {0}*'.format(workspace))
            raise

    id_pr = None
    scm = Github(GITHUB_INFO['login']['user'], GITHUB_INFO['login']['password'])

    # For backwards compatibility
    if job["git_branch"] == 'master':
        with lcd(os.path.join(workspace, 'ci')):
            config = json.loads(fetch_github_file('https://raw.githubusercontent.com/{0}/{1}/{2}/config.json'
                                                  .format(GITHUB_INFO["organization"],
                                                          GITHUB_INFO["repository"],
                                                          job["git_branch"]),
                                                  GITHUB_TOKEN))
            map_pkg = config['packages']
            git_diff = local('git diff HEAD~ HEAD --name-only', capture=True)
            git_diff = filter(None, list(set(git_diff.split('\n'))))
            dict_message_files = {}
            packages = {pkg['pkg_name']: pkg for pkg in map_pkg}
            modified_packages = {package_from_path(path, packages) for path in git_diff} - {None}
            exclude_dep = get_excluded_deps(packages, dict_message_files, modified_packages)
            logger_info('The following packages\' dependencies will be ignored if unmodified: {0}'
                        .format(exclude_dep))

            dep_graph = dependency_graph_from_modified_packages(workspace,
                                                                packages,
                                                                modified_packages,
                                                                exclude_dep)
    else:
        define_job_status_on_github_commit(commit_id,
                                           'pending',
                                           "", # Put an url
                                           context='Master Task - Task Launcher',
                                           description='Checking other Pull Requests for conflicts')
        id_pr = scm.search_pull_request_id(job["git_branch"])
        # Get relevant information from the pull request
        config, dep_graph, modified_packages = pull_request_information(id_pr, workspace)

        pull_requests = scm.get_pull_requests()
        pull_requests = filter(lambda prequest: prequest.mergeable, pull_requests)
        id_prs = {prequest.number: prequest for prequest in pull_requests}

        if detect_pr_collision:
            logger_info('Testing for inconsistencies in PR #{0}'.format(set(id_prs.keys()) - {id_pr}))
            original_pr = scm.get_pull_request(id_pr)

            for id_pr_other in set(id_prs.keys()) - {id_pr}:
                # If the other PR is more recent, do not check for inconsistency
                if id_prs[id_pr_other].created_at > original_pr.created_at:
                    logger_info('PR #{0} is more recent than #{1}'
                                .format(id_pr_other, id_pr))
                    continue
                try:  # We do not care for errors on other PRs
                    _, dep_graph_other, _ = pull_request_information(id_pr_other, workspace)
                except Exception as exc:
                    logger_error(traceback.format_exc())
                    logger_info('Got an exception on PR #{0}: {1}'.format(id_pr_other, exc))
                    continue
                nodes_intersect = set(dep_graph_other.nodes()) & set(dep_graph.nodes())

                if nodes_intersect:
                    logger_info('Intersecting packages: {0}'.format(nodes_intersect))
                    logger_info('Dependencies levels for tested PR #{0}: {1}'
                                .format(id_pr, gen_dependencies_level(dep_graph)))

                    define_job_status_on_github_commit(commit_id,
                                                       'error',
                                                       '',
                                                       context='Master Task - Task Launcher',
                                                       description=('Intersecting packages with PR #{0}: {1}'
                                                                    .format(id_pr_other, ', '.join(nodes_intersect))))
                    raise PullRequestCollision('PR #{0} has intersecting packages with PR #{1}: {2}'
                                               .format(id_pr_other, id_pr, nodes_intersect))

        map_pkg = config["packages"]
        packages = {pkg["pkg_name"]: pkg for pkg in map_pkg}

        do_not_touch_packages = get_do_not_touch_packages(id_pr, packages, scm, dep_graph, rebuild)

        # We can safely delete the nodes from the graph
        cleaned_dep_graph = copy.deepcopy(dep_graph)
        cleaned_dep_graph.remove_nodes_from(do_not_touch_packages)

        # Replace dep_lvl if we use another dep_graph
        _, dep_lvl_to_use, _ = gen_dependencies_level(cleaned_dep_graph)
        # Setting a green build for packages that should not be touched and are not in the build to keep traceability
        # Those packages are packages that were not affected by their loktar.dependency.
        for package in do_not_touch_packages:
            context = build_params_to_context(package, 'Not rebuilt')
            define_job_status_on_github_commit(commit_id, 'success', 'http://github.com', context,
                                               'Bro, this package seems damn fine.')

    no_problem, dep_lvl, name_graph_img = gen_dependencies_level(dep_graph, draw=True)

    if id_pr is not None:
        scm.create_pull_request_comment(id_pr,
                                        comment=u'Hey noobs, here go your dependency levels:\n\n```\n' +
                                                yaml.safe_dump(dep_lvl) +
                                                u'\n```\n' +
                                                u'![](https://raw.githubusercontent.com/{0}/ci_img/master/{1}.png)'
                                                .format(GITHUB_INFO["organization"], name_graph_img),
                                        check_unique=True)

    # Replace dep_lvl if we calculated another dep_lvl to use
    dep_lvl = dep_lvl if dep_lvl_to_use is None else dep_lvl_to_use

    logger_info('=' * 20)
    logger_info('Dependency levels used for this build')
    logger_info('=' * 20)
    logger_info(dep_lvl)
    logger_info('=' * 20)

    params = {
        'commit_id': commit_id,
        'committer': committer,
        'dep_lvl': serialize(dep_lvl),
        'job["git_branch"]': job["git_branch"],
        'modified_packages': serialize(modified_packages)
    }

    if no_problem:
        define_job_status_on_github_commit(commit_id,
                                           'success',
                                           '', # TODO put an url
                                           context='Master Task - Task Launcher',
                                           description='Task Manager succeeded!')

        # TODO (write information in the share memory)

        return {
            "commit_id": commit_id,
            "committer": committer,
            "test_env_path": workspace,
            "git_branch": job["git_branch"],
            "dep_lvl": dep_lvl
        }

    else:
        logger_error('dependency level problem encountered')
        define_job_status_on_github_commit(commit_id,
                                           'error',
                                           "", # put an url
                                           context='Master Task - Task Launcher',
                                           description='Dependency level problem encountered')


if __name__ == "__main__":
    worker()
