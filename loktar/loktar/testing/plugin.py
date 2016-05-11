from fabric.api import lcd
from fabric.api import settings
import sys
import yaml

from loktar.cmd import exe
from loktar.environment import ROOT_PATH
from loktar.exceptions import CITestFail
from loktar.exceptions import ForbiddenTimelineKey
from loktar.exceptions import SimplePluginErrorConfiguration
from loktar.log import Log


class SimplePlugin(object):
    def __init__(self, package_info):
        """Constructor for the SimplePlugin

        Args:
            package_info (dict): represent all informations for the target package in the config.json

        Raise:
            SimplePluginErrorConfiguration: An error occurred when a field is missing in the yaml file
        """
        self.plugin_name = str(sys.modules[self.__class__.__module__].__file__).split(".")[0]
        self.logger = Log()
        self.config = yaml.load(open("{0}.yaml".format(self.plugin_name)).read())

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

    def _base_run(self):
        """Run the command indicated in the yaml file in the package directory

        Raise:
            CITestFail: An error occurred when the test failed
        """
        with lcd(self.path):
            with settings(warn_only=True):
                result = exe(self.cmd, remote=False)
                if not result:
                    self.logger.error(result)
                    raise CITestFail('Test failed: {0}'.format(result))


class ComplexPlugin(SimplePlugin):
    def __init__(self, package_info):
        """Constructor for the ComplexPlugin, child of SimplePlugin

        Args:
            package_info (dict): represent all informations for the target package in the config.json

        Raise:
            SimplePlugin.SimplePluginErrorConfiguration: An error occurred when a field is missing in the yaml file
        """
        SimplePlugin.__init__(self, package_info)
        self.timeline = dict()
        self.share_memory = dict()
        self.__origin = {
            50: self._base_run
        }

    def _run(self, timeline):
        """Run the timeline

        Raise:
            ForbiddenTimelineKey: An error occurred when the plugin try to used a reserved key
        """
        try:
            assert not (set(self.__origin.keys()) & set(timeline))
        except AssertionError:
            raise ForbiddenTimelineKey("Timeline key: 50 is reserved")

        timeline.update(self.__origin)

        for ref in sorted(timeline):
            timeline[ref]()
