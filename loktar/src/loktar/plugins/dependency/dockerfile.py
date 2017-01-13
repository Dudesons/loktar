import os
import re


def docker_deps(basepath):
    """Get docker image dependencies.

    Args:
        basepath (str): Path to the package

    Returns:
        set: Dependencies names.
    """
    docker_file = os.path.join(basepath, "Dockerfile")
    if os.path.exists(docker_file):
        with open(docker_file, "r") as f:
            dockerfile = f.read()
        re_dockerfile = re.compile("FROM (.+)")
        docker_from = re_dockerfile.findall(dockerfile)
        assert len(docker_from) <= 1
        if docker_from:
            docker_from = docker_from[0]
            docker_image_name_tag = docker_from.rsplit("/", 1)[-1]
            docker_image_name = docker_image_name_tag.split(":", 1)[0]
            return {docker_image_name}
        else:
            return set()
    else:
        return set()

Plugin = docker_deps
