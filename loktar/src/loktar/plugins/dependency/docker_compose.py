import os
import yaml


def docker_compose_deps(basepath):
    """Get docker image dependencies.

    Args:
        basepath (str): Path to the package

    Returns:
        set: Dependencies names.
    """
    services = list()
    for docker_compose_file in [os.path.join(basepath, item) for item in os.listdir(basepath) if "docker-compose" in item]:
        with open(docker_compose_file) as fd:
            services.extend(yaml.safe_load(fd.read())["services"].keys())

    return set(filter(None, services))

Plugin = docker_compose_deps

