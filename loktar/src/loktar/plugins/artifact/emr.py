from loktar.exceptions import CIBuildPackageFail
from loktar.plugin import SimplePlugin


def run(*args, **kwargs):
    """This is a wrapper for running the plugin

    """
    try:
        plugin = EMR(*args)
        return plugin.get_result()
    except TypeError:
        print(EMR.__init__.__doc__)
        raise


class EMR(object):
    def __init__(self, artifact_info, remote):
        """Plugin for managing artifacts for aws emr

            Args:
                artifact_info (dict): Contains information about the package to execute inside the plugin
                remote (bool): Define if the plugin will be execute in remote or not

        """
        if artifact_info["build_info"]["input_type"] == "jar":
            self.__result = _Jar(artifact_info, remote).run()
        else:
            raise CIBuildPackageFail("the input type : '{}' is not managed, create a pr for integrate this input type"
                                     .format(artifact_info["build_info"]["input_type"]))

    def get_result(self):
        return self.__result


class _Jar(SimplePlugin):
    def __init__(self, artifact_info, remote):
        """Build the jar for a EMR, it is stored on s3

            Args:
                artifact_info (dict): Contains information about the package to execute inside the plugin
                remote (bool): Define if the plugin will be execute in remote or not
        """

        if artifact_info["mode"] == "master":
            s3cmd = "{} aws s3 cp ./target/ s3://{}/jars/prod/{}/ --recursive --exclude '*' --include '*.jar'".format(
                artifact_info["build_info"].get("prefix_command", ""),
                artifact_info["build_info"]["bucket_name"],
                artifact_info["artifact_name"]
            )
        else:
            s3cmd = "{} aws s3 cp ./target/ s3://{}/jars/dev/{}/{}/ --recursive --exclude '*' --include '*.jar'".format(
                artifact_info["build_info"].get("prefix_command", ""),
                artifact_info["build_info"]["bucket_name"],
                artifact_info["artifact_name"],
                artifact_info["mode"]
            )

        SimplePlugin.__init__(self, artifact_info,
                              {
                                  "command": {
                                      "run": s3cmd.strip(),
                                      "clean": artifact_info.get("clean_method", "make clean")
                                  }
                              },
                              remote=remote)

    def run(self):
        self._base_run()
        self._base_clean()
        return {
        }
