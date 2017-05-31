from copy import deepcopy

from loktar.exceptions import CIBuildPackageFail
from loktar.plugin import ComplexPlugin
from loktar.strategy_run import strategy_runner


def run(*args, **kwargs):
    """This is a wrapper for running the plugin

    """
    try:
        return Protobuff(args[0], args[1]).run()
    except IndexError:
        print(Protobuff.__init__.__doc__)
        raise


class Protobuff(ComplexPlugin):
        def __init__(self, artifact_info, remote):
            """Plugin for building protobuff project

                Args:
                    artifact_info (dict): Contains information about the package to execute inside the plugin
                    remote (bool): Define if the plugin will be execute in remote or not

                Raises:
                    CIBuildPackageFail: when one of the steps for packaging failed
            """
            ComplexPlugin.__init__(self, artifact_info,
                                   {
                                       "command": {
                                           "run": None,
                                           "clean": artifact_info.get("clean_method", "make clean")
                                       }
                                   },
                                   remote=remote)
            self.timeline = {
                10: self.launch_sub_project
            }
            self.share_memory["latest_versions"] = list()

        def run(self):
            """Default method for running the timeline

            """
            self._run()
            return {
                "versions": self.share_memory["latest_versions"]
            }

        def launch_sub_project(self):
            """

            """
            for artifact_type in self.artifact_info["build_info"]["sub_artifact_types"]:
                sub_artifact_config = deepcopy(self.artifact_info)
                sub_artifact_config["artifact_type"] = artifact_type["type"]
                result = strategy_runner(sub_artifact_config,
                                         "artifact",
                                         remote=artifact_type["remote"] if "remote" in artifact_type else False)

                if result is not None and "version" in result:
                    self.share_memory["latest_versions"].append("{}-{}-{}".format(sub_artifact_config["artifact_name"],
                                                                                  artifact_type["type"],
                                                                                  result["version"]))
