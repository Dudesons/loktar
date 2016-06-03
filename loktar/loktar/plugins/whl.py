from pypicloud_client.client import PypicloudClient

from loktar.cmd import exe
from loktar.cmd import exec_command_with_retry
from loktar.environment import MAX_RETRY_PYTHON_UPLOAD
from loktar.exceptions import WheelPackageFail
from loktar.plugin import ComplexPlugin


def run(*args, **kwargs):
    Whl(args[0]).run()


class Whl(ComplexPlugin):
        def __init__(self, package_info):
            ComplexPlugin.__init__(self, package_info,
                                   {
                                       "command": {
                                           "run": None,
                                           "clean": "make clean"
                                       }
                                   })
            self.timeline = {
                10: self.get_version,
                40: self.release
            }
            self.pypicloud = PypicloudClient()

        def run(self):
            """Default method for running the timeline
            """
            self._run()

        def get_version(self):
            pypicloud = PypicloudClient()
            if self.package_info["mode"] == "master":
                try:
                    self.share_memory["latest_version"] = str(int(filter(
                        lambda pkg: pkg.isdigit(),
                        sorted(
                            map(
                                lambda pkg: pkg["version"],
                                pypicloud.get_versions(self.package_info["pkg_name"])
                            ),
                            reverse=True
                        )
                    )[0]) + 1)
                except IndexError:
                    self.share_memory["latest_version"] = 1
            else:
                self.share_memory["latest_version"] = self.package_info["mode"]

        def release(self):
            """
            """
            with self.cwd(self.package_info["package_location"]):
                # Edit the package version
                if not exe("sed -i 's/VERSION = .*/VERSION = \"{0}\"/g' setup.py"
                           .format(self.share_memory["latest_version"]), remote=False):
                    raise WheelPackageFail("Failed to update the version")

                # Build package
                if not exec_command_with_retry("make release", max_retry=MAX_RETRY_PYTHON_UPLOAD, remote=False):
                    raise WheelPackageFail('Release failed')

                self.logger.info('Wheel package built & uploaded')
