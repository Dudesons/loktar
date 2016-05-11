import glob
import os

from loktar.exceptions import CITestFail
from loktar.exceptions import CITestUnknown
from loktar.exceptions import ImportPluginError
from loktar.log import Log


def run_test(packages, package_name):
    """Run the packaging functions

    Args:
        packages (dict): Dict of package_name: package_config
        package_name (str): Name of the package to test.

    Raises:
        CITestFail: some error occured during the test
        CITestUnknown: wrong value for config['test_type']
    """
    logger = Log()
    test_type = packages[package_name]['test_type']

    categories_test = dict()
    try:
        categories_test = {e: __import__("loktar.testing.{0}.{1}".format(e, e.capitalize()))
                           for e in filter(lambda x: x not in ["__init__", "plugin"],
                                           map(lambda x: x.split(".")[0].split("/")[-1],
                                               glob.glob("{0}/*.py"
                                                         .format(os.path.dirname(os.path.abspath(__file__))))))
                           if e not in categories_test}
    except ImportError as e:
        raise ImportPluginError(e)

    if test_type in categories_test:
        test_result = categories_test[test_type](packages, package_name).run()
        if test_result is not None and not test_result:
            logger.error("{0} failed".format(test_type.capitalize()))
            raise CITestFail

    else:
        logger.error("Unknown test type: {0}".format(test_type))
        raise CITestUnknown
