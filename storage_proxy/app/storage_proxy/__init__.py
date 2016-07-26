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



class MyExc(Exception):
    def __init__(self, message, *args):
        Exception.__init__(self, message, *args)
        self.reason = message
    def __str__(self):
        return "{}: {}".format(type(self).__name__, self.reason)

class CustomException(MyExc):
    """d"""
