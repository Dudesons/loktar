from loktar.constants import PLUGINS_INFO
from loktar.exceptions import CIBuildPackageFail
from loktar.exceptions import CITestFail
from loktar.exceptions import ImportPluginError
from loktar.log import Log
from loktar.plugin import find_plugin

ACCEPT_RUN_TYPE = ["test", "artifact", "dependency"]


def strategy_runner(package, run_type, remote=False, **kwargs):
    """Run the packaging functions

        Args:
            package (dict): package_config
            run_type (str): Represent the strategy to run on a package (test or artifact)
            remote (bool): Represent if the plugin is executed in remote or not, default value: False

        Raises:
            CITestFail: some error occurred during the test
            CITestUnknown: wrong value for config['test_type']
            CIBuildPackageFail: some error occurred during a packaging
            ImportPluginError: Fail to find / import a plugin
    """

    logger = Log()

    if run_type in ["test", "artifact"]:

        if run_type == "test" and package["test_type"] == "no-test":
            logger.info("Tag no-test detected, skip test")
            return {}

        params = {"type": "test_type", "exception": CITestFail}\
            if run_type == "test" else {"type": "artifact_type", "exception": CIBuildPackageFail}

        try:
            plugin = find_plugin(package[params["type"]],
                                 run_type,
                                 PLUGINS_INFO["locations"],
                                 PLUGINS_INFO["workspace"])
            logger.info("The plugin {} is loaded".format(package[params["type"]]))
        except ImportPluginError:
            raise

        logger.info("Starting {} plugin ...".format(package[params["type"]]))
        try:
            return plugin.run(package, remote)
        except Exception as e:
            logger.error(str(e))
            raise params["exception"](str(e))

    elif run_type == "dependency":
        dependencies = set(package.get("depends_on", []))

        for plugin_type in package["dependencies_type"]:
            try:
                plugin = find_plugin(plugin_type,
                                     run_type,
                                     PLUGINS_INFO["locations"],
                                     PLUGINS_INFO["workspace"])
                logger.info("The plugin {} is loaded".format(plugin_type))
            except ImportPluginError:
                raise

            dependencies |= plugin.Plugin(kwargs.get("basepath"))

        return dependencies
    else:
        raise ValueError("run_type must be equal to {}, actual value: {}".format(", ".join(ACCEPT_RUN_TYPE), run_type))
