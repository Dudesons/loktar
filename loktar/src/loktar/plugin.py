from fabric.api import cd
from fabric.api import lcd
from fabric.api import settings
import importlib
import sys

from loktar.cmd import exe
from loktar.constants import PLUGINS_INFO
from loktar.constants import ROOT_PATH
from loktar.decorators import retry
from loktar.exceptions import CITestFail
from loktar.exceptions import ForbiddenTimelineKey
from loktar.exceptions import ImportPluginError
from loktar.exceptions import SimplePluginErrorConfiguration
from loktar.log import Log


class SimplePlugin(object):
    def __init__(self, artifact_info, config, **kwargs):
        """Constructor for the SimplePlugin

            Args:
                artifact_info (dict): represent all informations for the target package in the config.json
                config (dict): this is the configuration plugin. It contains 2 keys 'run' & 'clean'.

            Raise:
                SimplePluginErrorConfiguration: An error occurred when a key is missing in the configuration
        """
        self.logger = Log()
        self.config = config
        self.remote = kwargs.get("remote", False)
        self.artifact_info = artifact_info
        self.cwd = lcd if self.remote is False else cd
        self.exit_code_on_clean_method = PLUGINS_INFO["clean_exit_code"]

        root_location = artifact_info["artifact_root_location"] if "artifact_root_location" in artifact_info else ROOT_PATH["container"]

        if "artifact_name" in artifact_info:
            if "artifact_dir" in artifact_info:
                self.path = "{0}/{1}/{2}".format(root_location,
                                                 artifact_info["artifact_dir"],
                                                 artifact_info["artifact_name"])
            else:
                self.path = "{0}/{1}".format(root_location,
                                             artifact_info["artifact_name"])
        else:
            if "artifact_dir" in artifact_info:
                self.path = "{0}/{1}".format(root_location,
                                             artifact_info["artifact_dir"])
            else:
                self.path = root_location

        try:
            assert "run" in self.config["command"] and "clean" in self.config["command"]
        except AssertionError:
            raise SimplePluginErrorConfiguration("The simple plugin configuration is incompleted,"
                                                 " check if run & clean keys are filled")

    def __command(self, cmd, force_return_code=None):
        """Run the command indicated in the yaml file in the package directory
            Args:
                cmd (str): the command that be executed
                force_return_code (bool): Force the return code if necessary

            Raise:
                CITestFail: An error occurred when the test failed
        """
        if cmd != "" and cmd is not None:
            with self.cwd(self.path):
                with settings(warn_only=True):
                    if not exe(cmd, remote=self.remote, force_return_code=force_return_code):
                        raise CITestFail("Test failed, on command: {}, remote: {}".format(cmd, self.remote))

    def _base_run(self):
        try:
            self.__command(self.config["command"]["run"])
        except CITestFail:
            self._base_clean()
            raise

    def _base_clean(self):
        self.__command(self.config["command"]["clean"], force_return_code=self.exit_code_on_clean_method)


class ComplexPlugin(SimplePlugin):
    def __init__(self, artifact_info, config, **kwargs):
        """Constructor for the ComplexPlugin, child of SimplePlugin

        Args:
            artifact_info (dict): represent all informations for the target package in the config.json
            config (dict): this is the configuration plugin. It contains 2 keys 'run' & 'clean'.

        Raise:
            SimplePluginErrorConfiguration: An error occurred when a key is missing in the configuration
        """
        SimplePlugin.__init__(self, artifact_info, config, **kwargs)
        self.timeline = dict()
        self.share_memory = dict()
        self.__origin = {
            50: self._base_run,
            95: self._base_clean
        }

    def _run(self):
        """Run the timeline

        Raise:
            ForbiddenTimelineKey: An error occurred when the plugin try to used a reserved key
        """
        try:
            assert not (set(self.__origin.keys()) & set(self.timeline))
        except AssertionError:
            raise ForbiddenTimelineKey("Timeline key: 50 & 95 are reserved")

        self.timeline.update(self.__origin)

        for ref in sorted(self.timeline):
            self.timeline[ref]()


def find_plugin(plugin_name, plugin_type, plugin_locations, workspace):
    """Try to retrieve a plugin

        Args:
            plugin_name (str): the plugin to search
            plugin_type (str): the type of plugin to fetch
            plugin_locations (list): locations of plugins
            workspace (str):  Plugins workspace for fetching plugins

        Raises:
            ImportPluginError: it raise if the plugin cannot import or the plugin is not found

        Returns
            module (module): return the plugin
    """
    sys.path += plugin_locations
    errors = list()
    logger = Log()

    logger.info("Searching plugin: {} in {} standard plugins".format(plugin_name, plugin_type))
    try:
        return importlib.import_module("loktar.plugins.{}.{}".format(plugin_type, plugin_name))
    except ImportError as e:
        logger.info("{} not found in standard plugin".format(plugin_name))
        errors.append(str(e))

    logger.info("Searching plugin: {} in {} custom plugins".format(plugin_name, plugin_type))
    try:
        return importlib.import_module("{}.{}.{}".format(workspace, plugin_type, plugin_name))
    except (ImportError, TypeError) as e:
        logger.info("{} not found in custom plugin".format(plugin_name))
        errors.append(str(e))
        logger.error("\n".join(errors))
        raise ImportPluginError("\n".join(errors))
