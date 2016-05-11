from __future__ import division

import logging
import random
import re
import time

import jenkins
from jenkinsapi.constants import STATUS_SUCCESS
from jenkinsapi.custom_exceptions import NotBuiltYet
from jenkinsapi.jenkins import Jenkins
from requests import HTTPError

from loktar.environment import GITHUB_INFO
from loktar.environment import JENKINS_PROTOCOL
from loktar.exceptions import CIJobFail
from loktar.log import Log
from loktar.notifications import define_job_status_on_github_commit
from loktar.scm import Github
from loktar.serialize import serialize

logger = logging.getLogger(__name__)

log = Log()


def ci_downstream(ci_config, pkg_name, type_task, params, job_format="{0} - {1}"):
    """Send a job to the ci

    Args:
        ci_config: part of the config.json file under the ``'jenkins'`` key
        pkg_name: name of the package to build
        type_task: apparently only ``'superman'``
        params: parameters sent to jenkins
    """
    ci_server = jenkins.Jenkins('{0}://{1}'.format(JENKINS_PROTOCOL,
                                                   ci_config['host']),
                                ci_config['user'],
                                ci_config['password'])
    ci_server.build_job(job_format.format(pkg_name, type_task), params)


def job_manager(ci_config,
                component,
                component_id,
                git_branch,
                commit_id,
                committer,
                test_env_path):
    """Build all the levels for a component

    Args:
        ci_config: part of the config.json file under the ``'jenkins'`` key
        component: a list of loktar.dependency levels. Example:
        [['my_firstlib'], ['microservice_depending on_my_firstlib']]
        component_id: string with component number/component name
        git_branch: git branch name to test / build
        commit_id: commit_id
        committer: name of the person which committed
        test_env_path: the path where the environment is store (eg: /tmp/toto)
    """
    types_build = ['test', 'artifact'] if git_branch != 'master' else ['artifactmaster']

    jenkins_instance = Jenkins('{0}://{1}'.format(JENKINS_PROTOCOL,
                                                  ci_config['host']),
                               username=ci_config['user'],
                               password=ci_config['password'])

    for actual_number_lvl, lvl in enumerate(component):
        for type_build in set(types_build) - {'artifactmaster'}:
            for package in lvl:

                context = build_params_to_context(package, type_build)
                define_job_status_on_github_commit(commit_id,
                                                   "pending",
                                                   'http://github.com',
                                                   context=context,
                                                   description='Build awaiting launch')

    for actual_number_lvl, lvl in enumerate(component):
        for type_build in types_build:
            log.info('Building {type_build} for component {component_id}, level {lvl}/{lvl_nb}'
                     .format(type_build=type_build,
                             component_id=component_id,
                             lvl=actual_number_lvl + 1,
                             lvl_nb=len(component)))
            launch_jobs(jenkins_instance,
                        commit_id,
                        committer,
                        git_branch,
                        lvl,
                        type_build,
                        test_env_path)


def split_on_condition(seq, condition):
    """Split an iterator on a condition

    Args:
        seq (iterator): Iterator to process
        condition (function): Function representing the condition

    Returns:
        tuple of list: first element is a list of elements for which ``condition`` is True, the second element is a list
        for which ``condition`` is False.
    """
    true_list, false_list = [], []
    for item in seq:
        (true_list if condition(item) else false_list).append(item)
    return true_list, false_list


def is_good(build):
    """Since jenkinsapi.Build.is_good is not good enough, I'm writing this one

    Args:
        build: instance of jenkinsapi.Build

    Returns:
        a boolean True or False
    """
    tries = 12
    while build._data['result'] is None and tries > 0:
        build.poll()
        time.sleep(0.5)
        tries -= 1
    return build._data['result'] == STATUS_SUCCESS


def launch_jobs(jenkins_instance,
                commit_id,
                committer,
                git_branch,
                lvl,
                type_build,
                test_env_path):

    """Launch the jobs defined through the loktar.dependency graph

    Args:
        jenkins_instance: instance of the jenkins class
        commit_id: commit_id
        committer: name of the person which committed
        git_branch: git branch name to test / build
        lvl: level being run
        type_build: 'test' or 'artifact'
        test_env_path: the location of the cloned test environment.
    """
    launched_queues = []
    for package in lvl:
        launched_queues.append(launch_queue(jenkins_instance,
                                            commit_id,
                                            committer,
                                            package,
                                            git_branch,
                                            type_build,
                                            test_env_path))

    scm = Github(GITHUB_INFO['login']['user'], GITHUB_INFO['login']['password'])
    pr_id = scm.search_pull_request_id(git_branch)

    # Get an instance of the queue
    queue_instance = jenkins_instance.get_queue()
    running_builds = []

    i = 1

    # While there are queued items and running builds
    while launched_queues + running_builds:
        # We check for the first stopping condition, which is that the Pull request received a new commit
        if pr_id is not None:
            pr = scm.get_pull_request(pr_id)
            commit_sha = pr.head.sha
            if commit_id != commit_sha:
                log.info('PR #{0} received a new commit! Stopping this build.'.format(pr_id))
                stop_all_jobs(launched_queues, queue_instance, running_builds)
                raise CIJobFail('New commit arrived: {0}'.format(commit_sha))

        # We update running builds and queues
        for queue_item in launched_queues:
            try:
                queue_item.poll()
                build = queue_item.get_build()
            except NotBuiltYet:
                logger.info('Item not built yet')
            except HTTPError:
                log.info('HTTP Error when querying idem {0}'.format(queue_item))
            else:
                running_builds.append(build)
                launched_queues.remove(queue_item)

        # Check if the builds are running + it updates their status
        running_builds, stopped_builds = split_on_condition(running_builds,
                                                            lambda build: build.is_running())

        if i % 20 == 0:
            log.info('Launched: {0}'.format(launched_queues))
            log.info('Running: {0}'.format(running_builds))
            log.info('Stopped: {0}'.format(stopped_builds))
        i += 1

        # We check for the second stopping condition, which is that a build failed
        failed_builds = filter(lambda build: not is_good(build), stopped_builds)
        if failed_builds:
            stop_all_jobs(launched_queues, queue_instance, running_builds)
            raise CIJobFail('Some builds failed: {0}'.format(failed_builds))

        # Sleep between 0.5 and 1s
        time.sleep(0.5 + random.randint(0, 500) / 1000)


def stop_all_jobs(launched_queues, queue_instance, running_builds):
    """Stop all jobs in queue or in the build pipe

    Args:
        launched_queues (list): list of queue items
        queue_instance (instance of jenkins.queues.Queue): instance of a Queue
        running_builds (list): list of running builds
    """
    # We delete queued jobs
    for queue_item in launched_queues:
        queue_instance.delete_item(queue_item)
    # And we stop running builds
    for build in running_builds:
        build.stop()


def launch_queue(jenkins_instance,
                 commit_id,
                 committer,
                 package,
                 git_branch,
                 type_build,
                 test_env_path):
    """Launch a CI queue

    Returns:
        jenkinsapi.queue.QueueItem: QueueItem instance
    """
    if type_build == 'artifactmaster':
        job_name = '{0} - {1}'.format(package, 'artifact')
    else:
        job_name = '{0} - {1}'.format(package, type_build)
    job = jenkins_instance[job_name]
    job_params = get_job_params(commit_id,
                                committer,
                                package,
                                git_branch,
                                type_build,
                                test_env_path)
    # Get a Queue instance which represents the new job build in the queue
    q = job.invoke(build_params=job_params)
    return q


def get_job_params(commit_id,
                   committer,
                   package,
                   git_branch,
                   type_build,
                   test_env_path):
    """Build the parameters to send to Jenkins jobs

    Args:
        commit_id:
        committer:
        package:
        git_branch:
        type_build:
        test_env_path:

    Returns:
    """
    composition_parameters = ('{0}:@:{1}'
                              .format(package,
                                      serialize(build_params_to_context(package, type_build)
                                                )
                                      )
                              )
    if type_build == 'test':
        job_params = {'package_name': composition_parameters,
                      'branch': ':@:'.join([git_branch,
                                            test_env_path,
                                            commit_id]),
                      'committer': committer}
    elif type_build == 'artifact':
        job_params = {'package_name': composition_parameters,
                      'branch': ':@:'.join([git_branch,
                                            test_env_path,
                                            commit_id]),
                      'committer': committer}
    elif type_build == 'artifactmaster':
        job_params = {'package_name': package,
                      'branch': git_branch,
                      'committer': committer}
    else:
        raise CIJobFail('Unknown type build {0}'.format(type_build))
    return job_params


def build_params_to_context(package, type_build):
    """Output a status message describing the build

    Args:
        package (str): Package being built
        type_build (str): type of build

    Returns:
        str: Message to use in Github status.
    """
    return ('{package} ({type_build})'
            .format(package=package, type_build=type_build))


def context_to_build_params(context):
    """Parse a Github status into the build parameters

    Args:
        context (basicstring): Github status message.

    Returns:
        package, type_build

    Raises:
        ValueError: Could not decode context
    """
    regex = re.compile('([\w\s-]+) \(([\w\s-]+)\)')
    groups = regex.findall(context)
    if not groups or len(groups[0]) != 2:
        raise ValueError('Could not decode context: "{0}". Regex groups: {1}'.format(context, groups))
    package, type_build = groups[0]
    return package, type_build
