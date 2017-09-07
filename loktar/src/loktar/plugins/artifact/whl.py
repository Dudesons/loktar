from pypicloud_client.client import PypicloudClient

from loktar.cmd import exe
from loktar.decorators import retry
from loktar.exceptions import CIBuildPackageFail
from loktar.plugin import ComplexPlugin


def run(*args, **kwargs):
    """This is a wrapper for running the plugin

    """
    try:
        return Whl(args[0], args[1]).run()
    except IndexError:
        print(Whl.__init__.__doc__)
        raise


class Whl(ComplexPlugin):
        def __init__(self, artifact_info, remote):
            """Plugin for building python wheel package

                Args:
                    artifact_info (dict): Contains information about the package to execute inside the plugin
                    remote (bool): Define if the plugin will be execute in remote or not

                Raises:
                    CIBuildPackageFail: when one of the steps for packaging or uploading the package failed
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
                10: self.get_next_version,
                40: self.release
            }
            self.pypicloud = PypicloudClient()

        def run(self):
            """Default method for running the timeline

            """
            self._run()
            return {
                "version": self.share_memory["latest_version"]
            }

        def get_next_version(self):
            """Get the next version for the current package

            """
            if self.artifact_info["mode"] == "master":
                try:
                    versions = filter(
                        lambda pkg_version: int(pkg_version.isdigit()),
                        map(
                            lambda pkg: pkg["version"],
                            self.pypicloud.get_versions(self.artifact_info["artifact_name"])
                        )
                    )

                    self.share_memory["latest_version"] = str(
                        sorted(
                            [int(version) for version in versions],
                            reverse=True
                        )[0] + 1
                    )

                except IndexError:
                    self.share_memory["latest_version"] = 1
            else:
                self.artifact_info["mode"] = self.artifact_info["mode"].replace("_", "-").replace("/", "-")
                self.share_memory["latest_version"] = "0.{0}".format(self.artifact_info["mode"])
                self.pypicloud.delete_package(self.artifact_info["artifact_name"], self.share_memory["latest_version"])

        @retry
        def release(self):
            """Create & upload the package

            """
            with self.cwd(self.path):
                # Edit the package version
                if not exe("sed -i 's/VERSION = .*/VERSION = \"{0}\"/g' setup.py"
                           .format(self.share_memory["latest_version"]), remote=self.remote):
                    raise CIBuildPackageFail("Failed to update the version")

                # Build package
                if not exe("make release", remote=self.remote):
                    raise CIBuildPackageFail("Release failed for the wheel package")

                self.logger.info("Wheel package built & uploaded")
