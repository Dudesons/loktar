import time

from boto.exception import S3ResponseError
from boto.dynamodb2 import connect_to_region as ddb_connect_to_region
from boto.rds import connect_to_region as rds_connect_to_region
from boto.s3 import connect_to_region as s3_connect_to_region
from boto.sqs import connect_to_region as sqs_connect_to_region
from boto.sqs.regioninfo import SQSRegionInfo
import docker
from etcd import Client as EtcdClient
from etcd import EtcdException
from etcd import EtcdConnectionFailed
from etcd import EtcdWatchTimedOut
import paramiko
from pymongo import MongoClient
import redis
import requests
import socket

from loktar.log import Log


logger = Log()


def wait_ssh(host="localhost", port=22, retries=30, sleep=10, **kwargs):
    """Wait for SSH service

    Args:
        host (Optional[str]): host name. Default to "localhost".
        port (Optional[int]): post to check. Defaults to 22.
        retries (int): Maximum number of retries. Defaults to 30.
        sleep (int): Time of sleep between retries, in seconds. Defaults to 10 seconds.

    Returns:
       bool: True if it is ready, False if something went wrong

    """
    ssh = paramiko.SSHClient()
    ssh.load_system_host_keys()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    for i in range(0, retries):
        try:
            if "password" in kwargs:
                ssh.connect(host, username=kwargs.get("user"), password=kwargs.get("password"), port=port)
            elif "key_file" in kwargs:
                ssh.connect(host, username=kwargs.get("user"), key_filename=kwargs.get("key_file"), port=port)
            elif "pkey" in kwargs:
                ssh.connect(host, username=kwargs.get("user"), pkey=kwargs.get("pkey"), port=port)
            else:
                raise ValueError("Keyword Argument missing (password or key_file or pkey)")
            return True
        except (paramiko.BadHostKeyException, paramiko.AuthenticationException,
                paramiko.SSHException, socket.error, socket.gaierror) as e:
            logger.warning(str(e))
            logger.warning("SSH server is not up yet")
            time.sleep(sleep)

    logger.error("Cannot connect to ssh server")
    logger.error("Aborting")
    return False


def wait_elasticsearch(host="localhost", port=9200, retries=30, sleep=10, secure=False, **kwargs):
    """Wait for Elasticsearch to be up.

    Args:
        host (str): Host name. Default to "localhost".
        port (int): Elasticsearch port. Defaults to 9200.
        retries (int): Maximum number of retries. Defaults to 30.
        sleep (int): Time of sleep between retries, in seconds. Defaults to 10 seconds.
        secure (bool): Secure communication. Defaults to False.

    Returns:
       bool: True if it is ready, False if something went wrong

    """
    for i in range(0, retries):
        try:
            res = requests.get("{}://{}:{}/_cluster/health".format("https" if secure else "http", host, port))
        except requests.exceptions.ConnectionError:
            logger.warning("ES is not up yet.")
            time.sleep(sleep)
            continue

        logger.info("ES is up, checking status.")
        health = res.json()["status"]
        if health in ["green", "yellow"]:
            return True
        else:
            logger.info("health status: {}".format(health))

    logger.error("Cannot connect to elasticsearch.")
    logger.error("Aborting")
    return False


def wait_mongo(host="localhost", port=27017, retries=30, sleep=10, **kwargs):
    """Wait for Mongo DB to be up.

    Args:
        host (Optional[str]): Host name. Default to "localhost".
        port (Optional[int]): Mongo DB port. Defaults to 27017.
        retries (Optional[int]): Maximum number of retries. Defaults to 30.
        sleep (Optional[int]): Time of sleep between retries, in seconds. Defaults to 10 seconds.

    Returns:
       bool: True if it is ready, False if something went wrong

    """
    client = MongoClient(host, port)

    for i in range(0, retries):
        try:
            client.server_info()
        except Exception as exc:
            logger.warning("Mongo is not up yet. Got exception {exc}".format(exc=exc))
            time.sleep(sleep)
            continue

        logger.info("Mongo is up, checking status.")
        return True

    logger.error("Cannot connect to mongo.")
    logger.error("Aborting")
    return False


def wait_redis(host="localhost", port=6379, retries=30, sleep=10, **kwargs):
    """Wait for Redis to be up.

    Args:
        host (Optional[str]): Host name. Default to "localhost".
        port (Optional[int]): Redis port. Defaults to 6379.
        retries (Optional[int]): Maximum number of retries. Defaults to 30.
        sleep (Optional[int]): Time of sleep between retries, in seconds. Defaults to 10 seconds.

    Returns:
       bool: True if it is ready, False if something went wrong

    """
    client = redis.StrictRedis(host=host, port=port)

    for i in range(0, retries):
        if client.ping():
            logger.info("Redis is up, checking status.")
            return True
        else:
            logger.warning("Redis is not up yet.")
            time.sleep(sleep)

    logger.error("Cannot connect to Redis.")
    logger.error("Aborting")
    return False


def wait_etcd(host="localhost", port=4001, retries=30, sleep=10, **kwargs):
    """Wait for etcd to be up.

    Args:
        host (Optional[str]): Host name. Default to "localhost".
        port (Optional[int]): Etcd port. Defaults to 6379.
        retries (Optional[int]): Maximum number of retries. Defaults to 30.
        sleep (Optional[int]): Time of sleep between retries, in seconds. Defaults to 10 seconds.

    Returns:
       bool: True if it is ready, False if something went wrong

    """
    def not_yet_up():
        """When etcd is not ready

        """
        logger.warning("Etcd is not up yet.")
        time.sleep(sleep)

    client = EtcdClient(host=host, port=port)

    for i in range(0, retries):
        try:
            response = client.stats
            if response["state"] == "StateLeader" and \
               response["leaderInfo"]["leader"] is not None and \
               response["leaderInfo"]["leader"] != "":
                logger.info("Etcd is up, checking status.")
                return True
            else:
                not_yet_up()
        except (EtcdException, EtcdConnectionFailed, EtcdWatchTimedOut, ValueError):
            not_yet_up()

    logger.error("Cannot connect to Etcd.")
    logger.error("Aborting")
    return False


def wait_dynamodb(host="localhost", port=8000, **kwargs):
    """"Wait for dynamodb to be up.

    Args:
        host (Optional[str]): Host name. Default to "localhost".
        port (Optional[int]): Dynamodb port. Defaults to 8000.

    Keyword Args:
        secure (bool): The communication is secure, default value False
        aws_access_key_id (str): Access key for aws (boto), default value foo
        aws_secret_access_key (str): Secret key for aws (boto), default value bar

    Returns:
       bool: True if it is ready, False if something went wrong

    """
    client = ddb_connect_to_region("eu-west-1",
                                   host=host,
                                   port=port,
                                   is_secure=kwargs.get("secure", False),
                                   aws_access_key_id=kwargs.get("aws_access_key_id", "foo"),
                                   aws_secret_access_key=kwargs.get("aws_secret_access_key", "bar"))

    try:
        logger.info("Waiting dynamodb (5min max internal boto retry)")
        client.list_tables()
    except socket.gaierror:
        logger.error("Cannot connect to Dynamodb.")
        logger.error("Aborting")
        return False

    logger.info("Dynamodb is ready")
    return True


def wait_sqs(host="localhost", port=9324, **kwargs):
    """"Wait for sqs to be up.

        Args:
            host (Optional[str]): Host name. Default to "localhost".
            port (Optional[int]): sqs port. Defaults to 8000.

        Keyword Args:
            fake_region (str): The fake region for you local sqs
            region (str): The region for the aws sqs
            secure (bool): The communication is secure, default value False
            aws_access_key_id (str): Access key for aws (boto), default value foo
            aws_secret_access_key (str): Secret key for aws (boto), default value bar

        Returns:
           bool: True if it is ready, False if something went wrong

        """
    if "fake_region" in kwargs:
        fake_region = SQSRegionInfo(name=kwargs.get("fake_region", "loktar"), endpoint=host)
        client = fake_region.connect(port=port,
                                     is_secure=kwargs.get("secure", False),
                                     aws_access_key_id=kwargs.get("aws_access_key_id", "foo"),
                                     aws_secret_access_key=kwargs.get("aws_secret_access_key", "bar"))
    else:
        client = sqs_connect_to_region(kwargs.get("region", "eu-west-1"),
                                       port=port,
                                       is_secure=kwargs.get("secure", False),
                                       aws_access_key_id=kwargs.get("aws_access_key_id", "foo"),
                                       aws_secret_access_key=kwargs.get("aws_secret_access_key", "bar"))

    try:
        logger.info("Waiting sqs (5min max internal boto retry)")
        client.get_all_queues()
    except socket.gaierror:
        logger.error("Cannot connect to sqs.")
        logger.error("Aborting")
        return False

    logger.info("sqs is ready")
    return True


def wait_rds(port=9324, **kwargs):
    client = rds_connect_to_region("eu-west-1",
                                   port=port,
                                   is_secure=kwargs.get("secure", False),
                                   aws_access_key_id=kwargs.get("aws_access_key_id", "foo"),
                                   aws_secret_access_key=kwargs.get("aws_secret_access_key", "bar"))

    try:
        logger.info("Waiting RDS (5min max internal boto retry)")
        client.get_all_dbinstances()
    except socket.gaierror:
        logger.error("Cannot connect to RDS.")
        logger.error("Aborting")
        return False

    logger.info("RDS is ready")
    return True


def wait_s3(host="localhost", port=4567, **kwargs):
    """"Wait for s3 to be up.

        Args:
            host (Optional[str]): Host name. Default to "localhost".
            port (Optional[int]): S3 port. Defaults to 8000.

        Keyword Args:
            secure (bool): The communication is secure, default value False
            aws_access_key_id (str): Access key for aws (boto), default value foo
            aws_secret_access_key (str): Secret key for aws (boto), default value bar

        Returns:
           bool: True if it is ready, False if something went wrong

        """
    client = s3_connect_to_region("eu-west-1",
                                  host=host,
                                  port=port,
                                  is_secure=kwargs.get("secure", False),
                                  aws_access_key_id=kwargs.get("aws_access_key_id", "foo"),
                                  aws_secret_access_key=kwargs.get("aws_secret_access_key", "bar"))

    try:
        logger.info("Waiting s3 (5min max internal boto retry)")
        client.get_all_buckets()
    except socket.gaierror:
        logger.error("Cannot connect to S3.")
        logger.error("Aborting")
        return False
    except S3ResponseError as e:
        if e.message == "The resource you requested does not exist"\
           and e.reason == "Not Found"\
           and e.status == 404:
            return True

    logger.info("S3 is ready")
    return True


def wait_http_services(host="localhost", port=80, retries=30, sleep=10, secure=False, **kwargs):
    """Wait for API to be up.

    Args:
        host (str): Host name. Default to "localhost".
        port (int): Service port. Defaults to 80.
        retries (int): Maximum number of retries. Defaults to 30.
        sleep (int): Time of sleep between retries, in seconds. Defaults to 10 seconds.
        secure (bool): Secure communication. Defaults to False.
        kwargs (dict): To pass additional check information
    Returns:
       bool: True if it is ready, False if something went wrong

    """
    for i in range(0, retries):
        try:
            res = requests.get("{}://{}:{}{}".format("https" if secure else "http", host, port, "/" if not kwargs.get("url_path") else "/" + kwargs.get("url_path")))
        except requests.exceptions.ConnectionError:
            logger.warning("{} service is not up yet.".format(kwargs.get("service_name") or 'UNNAMED'))
            time.sleep(sleep)
            continue

        logger.info("{} service is up, checking status.".format(kwargs.get("service_name") or 'UNNAMED'))
        health = res.status_code
        if health == 200:
            return True
        else:
            logger.info("health status: {}".format(health))

    logger.error("Cannot connect to service {}.".format(kwargs.get("service_name") or 'UNNAMED'))
    logger.error("Aborting")
    return False


def wait_docker_container(docker_client, container_id, retries=30, sleep=10):
    """Wait for a container is available.

    Args:
        docker_client (DockerClient): the docker client.
        container_id (str): the container id target.
        retries (int): Maximum number of retries. Defaults to 30.
        sleep (int): Time of sleep between retries, in seconds. Defaults to 10 seconds.
    Returns:
       bool: True if it is ready, False if something went wrong

    """
    for i in range(0, retries):
        try:
            container = docker_client.containers.get(container_id)
        except (docker.errors.ContainerError, docker.errors.ImageNotFound, docker.errors.APIError) as e:
            logger.error(str(e))
            return False

        if container.status == "running":
            logger.info("The container is running".format(container.status, container_id))
            return True
        elif container.status in ["dead", "exited", "removing"]:
            logger.error("The container have a problem, status={}, container_id={}".format(container.status,
                                                                                           container_id))
            return False
        else:
            logger.warning("The container is not yet up, status={}, container_id={}".format(container.status,
                                                                                            container_id))
            time.sleep(sleep)
            continue

    logger.error("The container can't start, status={}, container_id={}".format(container.status, container_id))
    logger.error("Aborting")
    return False
