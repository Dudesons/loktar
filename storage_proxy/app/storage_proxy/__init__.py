from loktar.exceptions import UnknownStorageMethod
from loktar.store import get_back_artifact


def get_artifact(storage_backend, bucket_name, artifact_name):
    """Get an uri for accessing to an artifact

    Args:
        storage_backend:
        bucket_name:
        artifact_name:

    Return:

    """
    try:
        artifact_location = get_back_artifact(storage_backend,
                                              artifact_name,
                                              aws_bucket=bucket_name,
                                              store_path="/artifacts")

        return artifact_location, 201

    except Exception as e:
        return str(e), 400
