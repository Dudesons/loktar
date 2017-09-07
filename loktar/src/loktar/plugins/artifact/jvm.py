from loktar.cmd import exec_with_output_capture
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
                plugin = _SBT(artifact_info, remote)
            elif artifact_info["build_info"]["build_type"] == "maven":
                plugin = _Maven(artifact_info, remote)
            else:
                raise CIBuildPackageFail("the build type: '{}' isn't managed, create a pr for integrate this build type"
                                         .format(artifact_info["build_info"]["build_type"]))
            self.__result = plugin.run()

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
            sbtcmd = "{} sbt 'release with-defaults skip-tests'".format(
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

        with self.cwd(self.path):
            rc, output = exec_with_output_capture("ls", remote=remote)
            if not rc:
                raise OSError(output.join("\n"))
            else:
                if "build.sbt" not in output:
                    rc, output = exec_with_output_capture("dirname $(find * -name build.sbt)", remote=remote)
                    if not rc:
                        raise CIBuildPackageFail("Can't find build.sbt")
                    else:
                        self.path = "{}/{}".format(self.path, output[0])

    def run(self):
        self._base_run()
        return {
        }


class _Maven(SimplePlugin):
    def __init__(self, artifact_info, remote):
        """Plugin for building jvm artifact with maven

            Args:
                artifact_info (dict): Contains information about the package to execute inside the plugin
                remote (bool): Define if the plugin will be execute in remote or not

            Raises:
                CIBuildPackageFail: when one of the steps for packaging or uploading the package failed
        """
        if artifact_info["mode"] == "master":
            sbtcmd = "{} mvn -Darguments=\"-DskipTests\" --batch-mode release:prepare release:perform".format(
                artifact_info["build_info"].get("prefix_command", "")
            )
        else:
            sbtcmd = "{} mvn -DskipTests deploy".format(
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
