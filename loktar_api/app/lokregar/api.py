import time

import docker

from loktar.db import Job
from loktar.environment import DOCKER_CI
from loktar.environment import DOCKER_ENGINE
DB = Job()


def init(scm_provider, payload):
    lokregar_payload = {"status": 0, "scm": scm_provider, "lastAccess": time.time()}
    lokregar_payload.update(payload)

    docker_client = docker.Client(base_url="{0}:{1}".format(DOCKER_ENGINE["address"], DOCKER_ENGINE["port"]))
    container_info = docker_client.create_container(DOCKER_CI, command="sleep 1000")
    docker_client.start(container=container_info['Id'])
    lokregar_payload["id"] = container_info['Id']

    if DB.set_job(container_info['Id'], lokregar_payload):
        return lokregar_payload, 201
    else:
        return 400


def get_jobs():
    return DB.get_jobs(), 201


def get_job(id):
    return DB.get_job(id), 201
