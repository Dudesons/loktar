from loktar.exceptions import CIBuildPackageFail
from loktar.plugin import SimplePlugin


def run(*args, **kwargs):
    """This is a wrapper for running the plugin

    """
    try:
        EMR(*args)
    except TypeError:
        print(EMR.__init__.__doc__)
        raise


class EMR(object):
    def __init__(self, package_info, remote):
        """Plugin for managing artifacts for aws emr

            Args:
                package_info (dict): Contains information about the package to execute inside the plugin
                remote (bool): Define if the plugin will be execute in remote or not

        """
        if package_info["build_info"]["input_type"] == "jar":
            _Jar(package_info, remote).run()
        else:
            raise CIBuildPackageFail("the input type : '{}' is not managed, create a pr for integrate this input type"
                                     .format(package_info["build_info"]["input_type"]))


class _Jar(SimplePlugin):
    def __init__(self, package_info, remote):
        """Build the jar for a EMR, it is stored on s3

            Args:
                package_info (dict): Contains information about the package to execute inside the plugin
                remote (bool): Define if the plugin will be execute in remote or not
        """

        if package_info["mode"] == "master":
            s3cmd = "{} aws s3 cp ./target/*jar s3://{}/jars/prod/{}/".format(
                package_info["build_info"].get("prefix_command", ""),
                package_info["build_info"]["bucket_name"],
                package_info["pkg_name"]
            )
        else:
            s3cmd = "{} aws s3 cp ./target/*jar s3://{}/jars/dev/{}/{}/".format(
                package_info["build_info"].get("prefix_command", ""),
                package_info["build_info"]["bucket_name"],
                package_info["pkg_name"],
                package_info["mode"]
            )

        SimplePlugin.__init__(self, package_info,
                              {
                                  "command": {
                                      "run": s3cmd.strip(),
                                      "clean": "make clean"
                                  }
                              },
                              remote=remote)

    def run(self):
        self._base_run()
