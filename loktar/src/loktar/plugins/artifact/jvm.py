from loktar.exceptions import CIBuildPackageFail
from loktar.plugin import SimplePlugin


def run(*args, **kwargs):
    """This is a wrapper for running the plugin

    """
    try:
        plugin = JVM(*args)
        return plugin.get_result()
    except TypeError:
        print(JVM.__init__.__doc__)
        raise


class JVM(object):
        def __init__(self, artifact_info, remote):
            """Plugin for managing artifacts for jvm world

            Args:
                artifact_info (dict): Contains information about the package to execute inside the plugin
                remote (bool): Define if the plugin will be execute in remote or not

            """
            if artifact_info["build_info"]["build_type"] == "sbt":
                self.__result = _SBT(artifact_info, remote).run()
            # elif artifact_info["build_info"]["build_type"] == "maven":
            #     self.__result = _MVN(artifact_info, remote).run()
            else:
                raise CIBuildPackageFail("the build type: '{}' isn't managed, create a pr for integrate this build type"
                                         .format(artifact_info["build_info"]["build_type"]))

        def get_result(self):
            return self.__result


class _SBT(SimplePlugin):
    def __init__(self, artifact_info, remote):
        """Plugin for building jvm artifact with sbt

            Args:
                artifact_info (dict): Contains information about the package to execute inside the plugin
                remote (bool): Define if the plugin will be execute in remote or not

            Raises:
                CIBuildPackageFail: when one of the steps for packaging or uploading the package failed
        """
        if artifact_info["mode"] == "master":
            sbtcmd = "{} sbt 'release with-defaults'".format(
                artifact_info["build_info"].get("prefix_command", "")
            )
        else:
            sbtcmd = "{} sbt publish".format(
                artifact_info["build_info"].get("prefix_command", "")
            )

        SimplePlugin.__init__(self, artifact_info,
                              {
                                  "command": {
                                      "run": sbtcmd.strip(),
                                      "clean": artifact_info.get("clean_method", "make clean")
                                  }
                              },
                              remote=remote)

    def run(self):
        self._base_run()
        return {
        }
