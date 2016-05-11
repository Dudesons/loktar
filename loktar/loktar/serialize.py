import base64
import pickle


def serialize(item):
    """Serialize an item

    Args:
        item (object): Python object

    Returns:
        str: The item serialized as a string
    """
    return base64.b64encode(pickle.dumps(item)).replace("=", "A")


def unserialize(item):
    """Unserialize an item

    Args:
        item (str): String to decode

    Returns:
        object: Python object
    """
    return pickle.loads(base64.b64decode(item))
