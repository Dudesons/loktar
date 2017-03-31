from docker import DockerClient

from loktar.check import wait_docker_container
from loktar.exceptions import CIJobFail


def start_container(image, environment, ports_settings, docker_endpoint="127.0.0.1:2375", network_mode="bridge"):
    """start a docker container

    Args:
        image (str): the image to instantiate
        environment (dict): describe the environment injected inide the container
        ports_settings (dict): Describe the port mapping between the host and the container
        docker_endpoint (str): the uri to the docker engine (default: 127.0.0.1:2375)
        network_mode (str): the network mode used for starting the container (default: bridge)

    Returns:
        A dict with the host ip, the host port bind on the container and the container id
    """
    container_infos = dict()
    client = DockerClient(base_url=docker_endpoint)

    client.images.pull(image)
    container = client.containers.run(image,
                                      detach=True,
                                      environment=environment,
                                      ports=ports_settings,
                                      network_mode=network_mode)
    container.start()

    if not wait_docker_container(client, container.id):
        raise CIJobFail("Fail to contact the container")

    container = client.containers.get(container.id)
    container_infos["host"] = container.attrs["Node"]["IP"] if "Node" in container.attrs else "127.0.0.1"
    container_infos["host_port"] = int(sorted(container.attrs["NetworkSettings"]["Ports"].values(),
                                              reverse=True)[0][0]["HostPort"])
    container_infos["id"] = container.id
    return container_infos


def clean_container(container_id, docker_endpoint="127.0.0.1:2375"):
    client = DockerClient(base_url=docker_endpoint)
    container = client.containers.get(container_id)

    container.kill()
    container.remove()


