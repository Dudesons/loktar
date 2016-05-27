from fabric.api import lcd
from fabric.api import settings
import importlib
import sys

from loktar.cmd import exe
from loktar.environment import ROOT_PATH
from loktar.exceptions import CITestFail
from loktar.exceptions import ForbiddenTimelineKey
from loktar.exceptions import ImportPluginError
from loktar.exceptions import SimplePluginErrorConfiguration
from loktar.log import Log


class SimplePlugin(object):
    def __init__(self, package_info, config):
        """Constructor for the SimplePlugin

        Args:
            package_info (dict): represent all informations for the target package in the config.json
            config (dict): this is the configuration plugin. It contains 2 keys 'run' & 'clean'.

        Raise:
            SimplePluginErrorConfiguration: An error occurred when a key is missing in the configuration
        """
        self.logger = Log()
        self.config = config

        try:
            self.path = package_info["test_location"]
        except KeyError:
            self.path = "{0}/{1}/{2}".format(ROOT_PATH["container"],
                                             package_info["pkg_dir"],
                                             package_info["pkg_name"]) \
                                             if "pkg_dir" in package_info else \
                                             "{0}/{1}".format(ROOT_PATH["container"],
                                                              package_info["pkg_name"])

        try:
            self.cmd = self.config["command"]
        except KeyError:
            raise SimplePluginErrorConfiguration()

    def __command(self, cmd):
        """Run the command indicated in the yaml file in the package directory

        Raise:
            CITestFail: An error occurred when the test failed
        """
        with lcd(self.path):
            with settings(warn_only=True):
                if not exe(cmd, remote=False):
                    raise CITestFail("Test failed")

    def _base_run(self):
        try:
            self.__command(self.cmd["run"])
        except CITestFail:
            self._base_clean()
            raise

    def _base_clean(self):
        self.__command(self.cmd["clean"])


class ComplexPlugin(SimplePlugin):
    def __init__(self, package_info, config):
        """Constructor for the ComplexPlugin, child of SimplePlugin

        Args:
            package_info (dict): represent all informations for the target package in the config.json
            config (dict): this is the configuration plugin. It contains 2 keys 'run' & 'clean'.

        Raise:
            SimplePluginErrorConfiguration: An error occurred when a key is missing in the configuration
        """
        SimplePlugin.__init__(self, package_info, config)
        self.timeline = dict()
        self.share_memory = dict()
        self.__origin = {
            50: self._base_run,
            95: self._base_clean
        }

    def _run(self, timeline):
        """Run the timeline
        Args:
            timeline (dict): represent the user timeline, it will be merged with the origin timeline

        Raise:
            ForbiddenTimelineKey: An error occurred when the plugin try to used a reserved key
        """
        try:
            assert not (set(self.__origin.keys()) & set(timeline))
        except AssertionError:
            raise ForbiddenTimelineKey("Timeline key: 50 & 95 are reserved")

        timeline.update(self.__origin)

        for ref in sorted(timeline):
            timeline[ref]()


def find_plugin(plugin_name, plugin_locations):
    """
    Args:
        plugin_name (str): the plugin to search
        plugin_locations (list): locations of plugins

    Raises:
        ImportPluginError: it raise if the plugin cannot import or the plugin is not found

    Returns
        module (module): return the plugin
    """
    sys.path += plugin_locations
    errors = list()
    logger = Log()

    try:
        return importlib.import_module("loktar.plugins.{0}".format(plugin_name))
    except ImportError as e:
        errors.append(str(e))

    try:
        return importlib.import_module(plugin_name)
    except ImportError as e:
        errors.append(str(e))
        logger.error("\n".join(errors))
        raise ImportPluginError