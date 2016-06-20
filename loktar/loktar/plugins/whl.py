from pypicloud_client.client import PypicloudClient

from loktar.cmd import exe
from loktar.cmd import exec_command_with_retry
from loktar.environment import MAX_RETRY_PYTHON_UPLOAD
from loktar.exceptions import CIBuildPackageFail
from loktar.plugin import ComplexPlugin


def run(*args, **kwargs):
    """This is a wrapper for running the plugin

    """
    try:
        Whl(args[0], args[1]).run()
    except IndexError:
        print(Whl.__init__.__doc__)
        raise


class Whl(ComplexPlugin):
        def __init__(self, package_info, remote):
            """Plugin for building python wheel package

                Args:
                    package_info (dict): Contains information about the package to execute inside the plugin
                    remote (bool): Define if the plugin will be execute in remote or not

                Raises:
                    WheelPackageFail: when one of the steps for packaging or uploading the package failed
            """
            ComplexPlugin.__init__(self, package_info,
                                   {
                                       "command": {
                                           "run": None,
                                           "clean": "make clean"
                                       }
                                   },
                                   remote=remote)
            self.timeline = {
                10: self.get_next_version,
                40: self.release
            }
            self.pypicloud = PypicloudClient()

        def run(self):
            """Default method for running the timeline

            """
            self._run()

        def get_next_version(self):
            """Get the next version for the current package

            """
            if self.package_info["mode"] == "master":
                try:
                    self.share_memory["latest_version"] = str(int(filter(
                        lambda pkg: pkg.isdigit(),
                        sorted(
                            map(
                                lambda pkg: pkg["version"],
                                self.pypicloud.get_versions(self.package_info["pkg_name"])
                            ),
                            reverse=True
                        )
                    )[0]) + 1)
                except IndexError:
                    self.share_memory["latest_version"] = 1
            else:
                self.share_memory["latest_version"] = "0.{0}".format(self.package_info["mode"])
                self.pypicloud.delete_package(self.share_memory["latest_version"])

        def release(self):
            """Create & upload the package

            """
            with self.cwd(self.package_info["package_location"]):
                # Edit the package version
                if not exe("sed -i 's/VERSION = .*/VERSION = \"{0}\"/g' setup.py"
                           .format(self.share_memory["latest_version"]), remote=self.remote):
                    raise CIBuildPackageFail("Failed to update the version")

                # Build package
                if not exec_command_with_retry("make release", max_retry=MAX_RETRY_PYTHON_UPLOAD, remote=self.remote):
                    raise CIBuildPackageFail("Release failed for the wheel package")

                self.logger.info("Wheel package built & uploaded")
