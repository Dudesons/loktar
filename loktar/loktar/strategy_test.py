from loktar.environment import PLUGINS_LOCATIONS
from loktar.exceptions import CITestFail
from loktar.exceptions import ImportPluginError
from loktar.log import Log
from loktar.plugin import find_plugin


def run_test(package):
    """Run the packaging functions

    Args:
        package (dict): package_config

    Raises:
        CITestFail: some error occured during the test
        CITestUnknown: wrong value for config['test_type']
    """
    logger = Log()
    plugins_location = PLUGINS_LOCATIONS.split(",") if type(PLUGINS_LOCATIONS) is str else PLUGINS_LOCATIONS
    try:
        # test_runner = eval("{0}.{1}".format(find_plugin(package["test_type"], plugins_location),
        #                                    package["test_type"].title().replace("_", "")))
        test_runner = find_plugin(package["test_type"], plugins_location)

    except ImportPluginError:
        raise

    try:
        test_runner.run(package)
    except Exception as e:
        logger.error(repr(e))
        raise CITestFail

