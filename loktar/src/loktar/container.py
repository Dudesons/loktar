from docker import DockerClient
import time


def start_container(image, environment, ports_settings, docker_endpoint="127.0.0.1:2375", network_mode="bridge"):
    container_infos = dict()
    client = DockerClient(base_url=docker_endpoint)
    container = client.containers.run(image,
                                      detach=True,
                                      environment=environment,
                                      ports=ports_settings,
                                      network_mode=network_mode)
    container.start()
    time.sleep(2)

    container = client.containers.get(container.id)
    container_infos["host"] = container.attrs["Node"]["IP"]
    container_infos["host_port"] = int(sorted(container.attrs["NetworkSettings"]["Ports"].values(),
                                              reverse=True)[0][0]["HostPort"])
    container_infos["id"] = container.id

    return container_infos


def clean_container(container_id, docker_endpoint="127.0.0.1:2375"):
    client = DockerClient(base_url=docker_endpoint)
    container = client.containers.get(container_id)
    container.kill()
    container.remove()


