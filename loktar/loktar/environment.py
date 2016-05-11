from fabric.api import env
import os


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
GITHUB_TOKEN = os.getenv("{0}GITHUB_TOKEN".format(PREFIX_ENV_VAR), '8b73920d962eb81240b47fc26ba205d94166d3bb')
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
