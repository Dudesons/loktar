import boto.s3 as s3

from loktar.decorators import retry
from loktar.constants import AWS
from loktar.exceptions import UnknownStorageMethod


@retry
def _store_artifact_on_s3(target, aws_region, aws_bucket, prefix_key_name=None):
    """Store an artifact on aws s3

    Args:
        target (str): this is the artifact target (eg: 1e827e44-f0a3-4f1f-a804-a28daff052af.tar.gz)
        aws_region (str, None): this is the aws region to connect for the bucket,
            aws_region can be set by a variable environment AWS_REGION, this variable it takes in first if it set
            can be set at None
        aws_bucket (str, None): this is the bucket name where the artifact will be stored
            aws_bucket can be set by a variable environment AWS_BUCKET, this variable it takes in first if it set
        prefix_key_name (str, None): This is a prefix key name in s3 for an object
            (eg: the bucket name is foo you want to store in bar the archive
            so prefix_key_name=bar to store in the foo bucket in the directory bar)


    Returns
        A string who debribes the artifact (eg: s3:@:foobar foobar here is the artifact name)
    """
    key_name = target.split("/")[-1] if prefix_key_name is None else "{}/{}".format(prefix_key_name,
                                                                                    target.split("/")[-1])
    connexion = s3.connect_to_region(AWS["REGION"] if AWS["REGION"] is not None else aws_region)
    bucket = connexion.get_bucket(AWS["BUCKET"] if AWS["BUCKET"] is not None else aws_bucket)
    key = bucket.new_key(key_name)
    key.set_contents_from_filename(target)

    return "s3:@:{0}".format(key_name)


def store_artifact(store_type, target, **kwargs):
    """Store the artifact for launching test

    Args:
        store_type (str): define the storage type
        target (str): this is the artifact target
        kwargs (dict): have some information around the storing method (eg: s3 need the bucket and region information)

    Returns
        A string who begin with the method for get back the artifact and the artifact name (eg: s3:@:foobar)
    """
    if store_type == "s3":
        return _store_artifact_on_s3(target, kwargs.get("aws_region", None),
                                     kwargs.get("aws_bucket", None),
                                     prefix_key_name=kwargs.get("prefix_key_name", None))
    else:
        raise UnknownStorageMethod("The storage: {} is unknown, open a PR for supporting the is storage"
                                   .format(store_type))


@retry
def _get_back_artifact_from_s3(target, aws_region, aws_bucket, store_path="/tmp"):
    """Get back an artifact from aws s3

        Args:
            target (str): this is the artifact target
            aws_region (str, None): this is the aws region to connect for the bucket,
                aws_region can be set by a variable environment AWS_REGION, this variable it takes in first if it set
                can be set at None
            aws_bucket (str, None): this is the bucket name where the artifact will be stored
                aws_bucket can be set by a variable environment AWS_BUCKET, this variable it takes in first if it set


        Returns
            A string who indicates where the artifact is stored (eg: s3:@:foobar foobar here is the artifact name)
    """
    artifact_location_to_store = store_path + "/" + target.split("/")[-1]
    connexion = s3.connect_to_region(AWS["REGION"] if AWS["REGION"] is not None else aws_region)
    bucket = connexion.get_bucket(AWS["BUCKET"] if AWS["BUCKET"] is not None else aws_bucket)
    key = bucket.get_key(target)
    key.get_contents_to_filename(artifact_location_to_store)

    return artifact_location_to_store


def get_back_test_env(test_env_location, **kwargs):
    """Get back an artifact from a source like aws s3, azure blob storage, remote dir ...

    Args:
        test_env_location (str): give information on the storage and the location of the artifact

    Raises:
        UnknownStorageMethod: The storage method is not recognized
    """
    storage_type, artifact = test_env_location.split(":@:")
    return get_back_artifact(storage_type, artifact, **kwargs)


def get_back_artifact(storage_type, artifact, **kwargs):
    """Get back an artifact from a source like aws s3, azure blob storage, remote dir ...

    Args:
        storage_type (str): the storage for to use for fetching the artifact
        artifact (str): the artifact name

    Raises:
        UnknownStorageMethod: The storage method is not recognized
    """

    if storage_type == "s3":
        return _get_back_artifact_from_s3(artifact, kwargs.get("aws_region", None),
                                          kwargs.get("aws_bucket", None),
                                          store_path=kwargs.get("store_path", "/tmp"))
    else:
        raise UnknownStorageMethod("The storage: {} is unknown, open a PR for supporting the is storage"
                                   .format(storage_type))
