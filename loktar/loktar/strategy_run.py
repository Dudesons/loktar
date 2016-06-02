from loktar.environment import PLUGINS_LOCATIONS
from loktar.exceptions import CITestFail
from loktar.exceptions import CIBuildPackageFail
from loktar.exceptions import ImportPluginError
from loktar.log import Log
from loktar.plugin import find_plugin


def strategy_runner(package, run_type):
    """Run the packaging functions

    Args:
        package (dict): package_config
        run_type (str): Represent the strategy to run on a package (test or artifact)

    Raises:
        CITestFail: some error occurred during the test
        CITestUnknown: wrong value for config['test_type']
        CIBuildPackageFail: some error occurred during a packaging
        ImportPluginError: Fail to find / import a plugin
    """

    if run_type not in ["test", "build"]:
        raise ValueError("run_type must be equal to 'test' or 'build', actual value: {0}".format(run_type))

    logger = Log()
    params = {"type": "test_type", "exception": CITestFail}\
        if run_type == "test" else {"type": "pkg_type", "exception": CIBuildPackageFail}
    plugins_location = PLUGINS_LOCATIONS.split(",") if type(PLUGINS_LOCATIONS) is str else PLUGINS_LOCATIONS
    try:
        runner = find_plugin(package[params["type"]], plugins_location)

    except ImportPluginError:
        raise

    try:
        runner.run(package)
    except Exception as e:
        logger.error(repr(e))
        raise params["exception"]

