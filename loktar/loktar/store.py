import boto.s3 as s3

from loktar.decorators import retry
from loktar.environment import AWS
from loktar.exceptions import UnknownStorageMethod


@retry
def _store_test_env_on_s3(target, aws_region, aws_bucket):
    """Store an archive on aws s3

    Args:
        target (str): this is the archive target (eg: 1e827e44-f0a3-4f1f-a804-a28daff052af.tar.gz)
        aws_region (str, None): this is the aws region to connect for the bucket,
            aws_region can be set by a variable environment AWS_REGION, this variable it takes in first if it set
            can be set at None
        aws_bucket (str, None): this is the bucket name where the archive will be stored
            aws_bucket can be set by a variable environment AWS_BUCKET, this variable it takes in first if it set


    Returns
        A string who debribes the archive (eg: s3:@:foobar foobar here is the archive name)
    """
    key_name = target.split("/")[-1]
    connexion = s3.connect_to_region(AWS["REGION"] if AWS["REGION"] is not None else aws_region)
    bucket = connexion.get_bucket(AWS["BUCKET"] if AWS["BUCKET"] is not None else aws_bucket)
    key = bucket.new_key(key_name)
    key.set_contents_from_filename(target)

    return "s3:@:{0}".format(key_name)


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
        return _store_test_env_on_s3(target, kwargs.get("aws_region", None), kwargs.get("aws_bucket", None))
    else:
        raise UnknownStorageMethod


@retry
def _get_back_test_env_from_s3(target, aws_region, aws_bucket):
    """Get back an archive from aws s3

        Args:
            target (str): this is the archive target
            aws_region (str, None): this is the aws region to connect for the bucket,
                aws_region can be set by a variable environment AWS_REGION, this variable it takes in first if it set
                can be set at None
            aws_bucket (str, None): this is the bucket name where the archive will be stored
                aws_bucket can be set by a variable environment AWS_BUCKET, this variable it takes in first if it set


        Returns
            A string who indicates where the archive is stored (eg: s3:@:foobar foobar here is the archive name)
    """
    test_env_location_ci = "/tmp/{0}".format(target)
    connexion = s3.connect_to_region(AWS["REGION"] if AWS["REGION"] is not None else aws_region)
    bucket = connexion.get_bucket(AWS["BUCKET"] if AWS["BUCKET"] is not None else aws_bucket)
    key = bucket.get_key(target)
    key.get_contents_to_filename(test_env_location_ci)

    return test_env_location_ci


def get_back_test_env(test_env_location, **kwargs):
    """Get back an archive from a source like aws s3, azure blob storage, remote dir ...

    Args:
        test_env_location (str): give information on the storage and the location of the archive

    Raises:
        UnknownStorageMethod: The storage method is not recognized
    """
    storage_type, archive = test_env_location.split(":@:")
    if storage_type == "s3":
        return _get_back_test_env_from_s3(archive, kwargs.get("aws_region", None), kwargs.get("aws_bucket", None))
    else:
        raise UnknownStorageMethod
