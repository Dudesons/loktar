from fabric.api import env
from fabric.api import lcd
from fabric.api import local
from fabric.exceptions import NetworkError
import json
import os
from uuid import uuid4

from loktar.cmd import exec_command_with_retry
from loktar.exceptions import PrepareEnvFail
from loktar.log import Log

env.disable_known_hosts = True
env.warn_only = True

PREFIX_ENV_VAR = "LOKTAR_"

# DEBIAN PACKAGE INFORMATION
CODE_NAME = os.getenv("{0}CODE_NAME".format(PREFIX_ENV_VAR), "rc")
COMPENANT = os.getenv("{0}COMPENANT".format(PREFIX_ENV_VAR), "main")
DEBIAN_REPOSITORY = os.getenv("{0}DEBIAN_REPOSITORY".format(PREFIX_ENV_VAR), None)

# About retry on command or http requests ...
MAX_RETRY_PYTHON_UPLOAD = os.getenv("{0}MAX_RETRY_PYTHON_UPLOAD".format(PREFIX_ENV_VAR), 3)
MAX_RETRY_DEBIAN_UPLOAD = os.getenv("{0}MAX_RETRY_DEBIAN_UPLOAD".format(PREFIX_ENV_VAR), 3)
MAX_RETRY_DOCKER_BUILD = os.getenv("{0}MAX_RETRY_DOCKER_BUILD".format(PREFIX_ENV_VAR), 3)
MAX_RETRY_DOCKER_PUSH = os.getenv("{0}MAX_RETRY_DOCKER_PUSH".format(PREFIX_ENV_VAR), 3)
MAX_RETRY_GITHUB = os.getenv("{0}MAX_RETRY_GITHUB".format(PREFIX_ENV_VAR), 3)

CONSUL = os.getenv("CONSUL", None)

GITHUB_INFO = {
    "login": {
        "user": os.getenv("{0}GITHUB_INFO_LOGIN_USER".format(PREFIX_ENV_VAR), None),
        "password": os.getenv("{0}GITHUB_INFO_LOGIN_PASSWORD".format(PREFIX_ENV_VAR), None)
    },
    "organization": os.getenv("{0}GITHUB_INFO_ORGANIZATION".format(PREFIX_ENV_VAR), None),
    "repository": os.getenv("{0}GITHUB_INFO_REPOSITORY".format(PREFIX_ENV_VAR), None),
    "notification": {
        "pending": os.getenv("{0}GITHUB_INFO_NOTIFICATION_PENDING".format(PREFIX_ENV_VAR),
                             "The build is running. If i was you I would leave quickly"),
        "success": os.getenv("{0}GITHUB_INFO_NOTIFICATION_SUCCESS".format(PREFIX_ENV_VAR),
                             "The build succeded! You're not so bad after all"),
        "error": os.getenv("{0}GITHUB_INFO_NOTIFICATION_ERROR".format(PREFIX_ENV_VAR),
                           "Error! I won't lie, you're really bad"),
        "failure": os.getenv("{0}GITHUB_INFO_NOTIFICATION_FAILLURE".format(PREFIX_ENV_VAR),
                             "Failure. Nobody is happy."),
        "unknown": os.getenv("{0}GITHUB_INFO_NOTIFICATION_UNKNOWN".format(PREFIX_ENV_VAR),
                             "Unknown state, so 42.")
    },
    "default_master_branch": os.getenv("{0}GITHUB_DEFAULT_MASTER_BRANCH".format(PREFIX_ENV_VAR), "master"),
    "manifest_path": os.getenv("{0}GITHUB_MANIFEST_PATH".format(PREFIX_ENV_VAR), "Manifest")
}
GITHUB_TOKEN = os.getenv("{0}GITHUB_TOKEN".format(PREFIX_ENV_VAR), None)
GITHUB_API_COMMITS = {
    "url": "https://api.github.com/repos/{0}/{1}/git/commits".format(GITHUB_INFO["organization"],
                                                                     GITHUB_INFO["repository"]),
    "headers": {
        "Authorization": "token {0}",
        "Accept": os.getenv("{0}GITHUB_API_COMMITS_HEADERS_ACCEPT".format(PREFIX_ENV_VAR),
                            "application/vnd.github-commitcomment.full+json")
    }
}
CONFIG_CI_FILE = os.getenv("{0}CONFIG_CI_FILE".format(PREFIX_ENV_VAR), "config.json")

ROOT_PATH = {
    "jenkins": os.getenv("{0}ROOT_PATH_JENKINS".format(PREFIX_ENV_VAR), "/var/lib/jenkins"),
    "container": os.getenv("{0}ROOT_PATH_CONTAINER".format(PREFIX_ENV_VAR), None),
    "build": os.getenv("{0}ROOT_PATH_BUILD".format(PREFIX_ENV_VAR), None)
}

JENKINS = {
    "host": os.getenv("{0}JENKINS_HOST".format(PREFIX_ENV_VAR), None),
    "user": os.getenv("{0}JENKINS_USER".format(PREFIX_ENV_VAR), None),
    "password": os.getenv("{0}JENKINS_PASSWORD".format(PREFIX_ENV_VAR), None)
}

SLAVE_ENVIRONMENT = {
    "PATH": "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:{0}/.local/bin"
            .format(ROOT_PATH["container"]),
    "env_file": os.getenv("{0}ENV_FILE".format(PREFIX_ENV_VAR), None)
}

AWS = {
    "REGION": os.getenv("{0}AWS_REGION".format(PREFIX_ENV_VAR), None),
    "BUCKET": os.getenv("{0}AWS_BUCKET".format(PREFIX_ENV_VAR), None)
}

PLUGINS_LOCATIONS = os.getenv("{0}PLUGINS_LOCATIONS".format(PREFIX_ENV_VAR), [])

SLACK = {
    "token": os.getenv("{0}SLACK_TOKEN".format(PREFIX_ENV_VAR), None),
    "channel": os.getenv("{0}SLACK_CHANNEL".format(PREFIX_ENV_VAR), None)
}

QUAY = {
    "limit": os.getenv("{0}QUAY_LIMIT".format(PREFIX_ENV_VAR), 100)
}

RETRY_HTTP = {
    "multiplier": os.getenv("{0}RETRY_HTTP_MULTIPLIER".format(PREFIX_ENV_VAR), 1.5),
    "interval": os.getenv("{0}RETRY_HTTP_INTERVAL".format(PREFIX_ENV_VAR), 0.5),
    "randomization_factor": os.getenv("{0}RETRY_HTTP_RANDOMIZATION_FACTOR".format(PREFIX_ENV_VAR), 0.5),
    "max_sleep_time": os.getenv("{0}RETRY_HTTP_MAX_SLEEP_TIME".format(PREFIX_ENV_VAR), 180)
}

STORAGE_PROXY = {
    "host": os.getenv("{0}STORAGE_PROXY_HOST".format(PREFIX_ENV_VAR), None),
    "port": os.getenv("{0}STORAGE_PROXY_PORT".format(PREFIX_ENV_VAR), None)
}

CI = {
  "external_fqdn": os.getenv("{0}CI_EXTERNAL_FQDN".format(PREFIX_ENV_VAR), None)
}


def prepare_test_env(branch, **kwargs):
    """Prepare the test environment

    Args:
        branch (str): Name of the branch the repository should be checkout to.

    Keyword Args:
        github_organization (str): this is the github organization for get back the repository, default value None.
                                   Also can be set by environment variable LOKTAR_GITHUB_INFO_ORGANIZATION
        github_repository (str): this is the target repository to download, default value None
                                 Also can be set by environment variable LOKTAR_GITHUB_INFO_REPOSITORY

    Raises:
        PrepareEnvFail: Failed to prepare the environment.
    """
    logger = Log()
    unique_name_dir = str(uuid4())
    unique_path_dir = "/tmp/{0}".format(unique_name_dir)
    archive = "{0}.tar.gz".format(unique_name_dir)
    logger.info("Preparing the test environment")

    github_organization = kwargs.get("github_organization", GITHUB_INFO["organization"])
    github_repository = kwargs.get("github_repository", GITHUB_INFO["repository"])

    os.mkdir(unique_path_dir)
    try:
        if not exec_command_with_retry("git clone -b {0} --single-branch git@github.com:{1}/{2}.git {3}"
                                       .format(branch, github_organization, github_repository, unique_path_dir),
                                       0,
                                       MAX_RETRY_GITHUB):
            raise PrepareEnvFail("The git clone can't the repository: {}/{}, check if you have the correct crendentials"
                                 .format(github_organization, github_repository))

        with lcd(unique_path_dir):
            if not exec_command_with_retry("git fetch origin master", 0, MAX_RETRY_GITHUB):
                raise PrepareEnvFail

            if branch != "master":
                if not exec_command_with_retry("git config --global user.email 'you@example.com'", 0, MAX_RETRY_GITHUB):
                    raise PrepareEnvFail

                if not exec_command_with_retry("git config --global user.name 'Your Name'", 0, MAX_RETRY_GITHUB):
                    raise PrepareEnvFail

                if not exec_command_with_retry("git merge --no-ff --no-edit FETCH_HEAD", 0, MAX_RETRY_GITHUB):
                    raise PrepareEnvFail

                local("rm -rf {0}/.git".format(unique_path_dir))

        with lcd("/tmp"):
            if not exec_command_with_retry("tar -czf {0} {1}".format(archive, unique_name_dir), 0, MAX_RETRY_GITHUB):
                raise PrepareEnvFail

        logger.info("The test env is ready!")

    except NetworkError as exc:
        logger.error(exc)
        raise
    except PrepareEnvFail:
        local("rm -rf {0}*".format(unique_path_dir))
        raise

    return "/tmp/{0}".format(archive)


def get_config(package_name, test_env_path, full=False):
    """Retrieve the test configuration

    Args:
        package_name: Name of the package for which to apply ``full=False``
        test_env_path: the location of the cloned test environment.
        full (boolean): See ``Returns`` section

    Returns:
        if ``full`` True, return the complete config.json file.
        Otherwise, return a dict with keys: ``['pkg_name', 'pkg_type', 'test_type']``
    """
    pkg_config = {}
    logger = Log()

    with lcd('{0}'.format(test_env_path)):
        config = json.loads(local('cat config.json', capture=True))

    logger.info('Parsing configuration')
    if not full:
        for package in config['packages']:
                if package['pkg_name'] == package_name:
                    pkg_config = package
                    break
    else:
        pkg_config = config

    logger.info('Conf is ok and has keys {0}'.format(pkg_config.keys()))
    return pkg_config
