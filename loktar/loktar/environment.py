import boto.s3 as s3
from fabric.api import env
from fabric.api import lcd
from fabric.api import local
from fabric.exceptions import NetworkError
import json
import os
from uuid import uuid4

from loktar.cmd import exec_command_with_retry
from loktar.decorators import retry
from loktar.exceptions import PrepareEnvFail
from loktar.exceptions import UnknownStorageMethod
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

JENKINS_PROTOCOL = os.getenv("{0}JENKINS_PROTOCOL".format(PREFIX_ENV_VAR), "http")
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
DOCKER_ENGINE = {
    "address": os.getenv("{0}DOCKER_CI_ADDRESS", "127.0.0.1"),
    "port": os.getenv("{0}DOCKER_CI_PORT", 2375),
    "registry_url": os.getenv("{0}DOCKER_CI_REGISTRY", None)
}
DOCKER_CI = {
    "registry": os.getenv("{0}DOCKER_CI_REGISTRY".format(PREFIX_ENV_VAR), None),
    "image": os.getenv("{0}DOCKER_CI_IMAGE".format(PREFIX_ENV_VAR), None),
    "acceptance_image": os.getenv("{0}DOCKER_CI_IMAGE".format(PREFIX_ENV_VAR), None),
    "base_image": os.getenv("{0}DOCKER_CI_BASE_IMAGE".format(PREFIX_ENV_VAR), None),
    "user": os.getenv("{0}DOCKER_CI_USER".format(PREFIX_ENV_VAR), None),
    "address_build": os.getenv("{0}DOCKER_CI_ADDRESS_BUILD".format(PREFIX_ENV_VAR), None),
    "services": os.getenv("{0}DOCKER_CI_SERVICES".format(PREFIX_ENV_VAR), None),
}
ROOT_PATH = {
    "jenkins": os.getenv("{0}ROOT_PATH_JENKINS".format(PREFIX_ENV_VAR), "/var/lib/jenkins"),
    "container": os.getenv("{0}ROOT_PATH_CONTAINER".format(PREFIX_ENV_VAR), None),
    "build": os.getenv("{0}ROOT_PATH_BUILD".format(PREFIX_ENV_VAR), None)
}
BUILD_PACKAGE = {
    "wheel": os.getenv("{0}BUILD_PACKAGE_WHEEL".format(PREFIX_ENV_VAR), "python setup.py bdist_wheel"),
    "debian": os.getenv("{0}BUILD_PACKAGE_DEBIAN".format(PREFIX_ENV_VAR), "dpkg --build"),
    "docker": os.getenv("{0}BUILD_PACKAGE_DOCKER".format(PREFIX_ENV_VAR),
                        "docker build --no-cache -t {0}".format(DOCKER_ENGINE["registry_url"]))
}

PUSH_PACKAGE = {
    "pypicloud": os.getenv("{0}PUSH_PACKAGE_PYPICLOUD".format(PREFIX_ENV_VAR), "twine upload -r pypicloud *whl"),
    "debian": os.getenv("{0}PUSH_PACKAGE_DEBIAN".format(PREFIX_ENV_VAR),
                        "deb-s3 upload -p -b {0} -c {1} -m {2} -v public -a amd64 *.deb"
                        .format(DEBIAN_REPOSITORY, CODE_NAME, COMPENANT)),
    "docker": os.getenv("{0}PUSH_PACKAGE_DOCKER".format(PREFIX_ENV_VAR),
                        "docker push {0}".format(DOCKER_ENGINE["registry_url"]))
}

JENKINS = {
    "host": "delivery.net:8080",
    "user": "lokbot",
    "password": "L39yN@;y6+We"
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


def prepare_test_env(branch, github_organization=None, github_repository=None):
    """Prepare the test environment

    Args:
        branch (str): Name of the branch the repository should be checkout to.
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

    logger.info("Preparing the test environment")

    os.mkdir(unique_path_dir)
    try:
        if not exec_command_with_retry("git clone -b {0} --single-branch git@github.com:{1}/{2}.git {3}"
                                       .format(branch,
                                               GITHUB_INFO["organization"]
                                               if github_organization is None else
                                               github_organization,
                                               GITHUB_INFO["repository"]
                                               if github_repository is None else
                                               github_repository,
                                               unique_path_dir),
                                       0,
                                       MAX_RETRY_GITHUB):
            raise PrepareEnvFail

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
            if not exec_command_with_retry("tar -czf {0}.tar.gz {0}".format(unique_name_dir), 0, MAX_RETRY_GITHUB):
                raise PrepareEnvFail

        logger.info("The test env is ready!")

    except NetworkError as exc:
        logger.error(exc)
        raise
    except PrepareEnvFail:
        local("rm -rf {0}*".format(unique_path_dir))
        raise

    return unique_path_dir


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


@retry
def store_test_env_on_s3(target, aws_region, aws_bucket):
    """Store an archive on aws s3

    Args:
        target (str): this is the archive target
        aws_region (str, None): this is the aws region to connect for the bucket,
            aws_region can be set by a variable environment AWS_REGION, this variable it takes in first if it set
            can be set at None
        aws_bucket (str, None): this is the bucket name where the archive will be stored
            aws_bucket can be set by a variable environment AWS_BUCKET, this variable it takes in first if it set


    Returns
        A string who debribes the archive (eg: s3:@:foobar foobar here is the archive name)
    """
    key_name = "{0}.tar.gz".format(target.split("/")[-1])
    connexion = s3.connect_to_region(AWS["REGION"] if AWS["REGION"] is not None else aws_region)
    bucket = connexion.get_bucket(AWS["BUCKET"] if AWS["BUCKET"] is not None else aws_bucket)
    key = bucket.new_key(key_name)
    key.set_contents_from_filename("{0}.tar.gz".format(target))

    return "s3:{0}".format(key_name)


def store_test_env(store_type, target, **kwargs):
    """Store the archive for launching test

    Args:
        store_type (str): define the storage type
        target (str): this is the archive target
        kwargs (dict): have some information around the storing method (eg: s3 need the bucket and region information)

    Returns
        A string who begin with the method for get back the archive and the archive name (eg: s3:@:foobar)
    """
    if store_type == "s3":
        return store_test_env_on_s3(target, kwargs.get("aws_region", None), kwargs.get("aws_bucket", None))
    else:
        raise UnknownStorageMethod


def get_back_test_env_from_s3(target, aws_region, aws_bucket):
    """Store an archive on aws s3

        Args:
            target (str): this is the archive target
            aws_region (str, None): this is the aws region to connect for the bucket,
                aws_region can be set by a variable environment AWS_REGION, this variable it takes in first if it set
                can be set at None
            aws_bucket (str, None): this is the bucket name where the archive will be stored
                aws_bucket can be set by a variable environment AWS_BUCKET, this variable it takes in first if it set


        Returns
            A string who debribes the archive (eg: s3:@:foobar foobar here is the archive name)
    """
    test_env_location_ci = "/tmp/{0}".format(target)
    connexion = s3.connect_to_region(AWS["REGION"] if AWS["REGION"] is not None else aws_region)
    bucket = connexion.get_bucket(AWS["BUCKET"] if AWS["BUCKET"] is not None else aws_bucket)
    key = bucket.get_key(target)
    key.get_contents_to_filename(test_env_location_ci)

    return test_env_location_ci


def get_back_test_env(test_env_location, **kwargs):
    storage_type, archive = test_env_location.split(":")
    if storage_type == "s3":
        return get_back_test_env_from_s3(archive, kwargs.get("aws_region", None), kwargs.get("aws_bucket", None))
    else:
        raise UnknownStorageMethod
