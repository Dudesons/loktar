import json

from loktar.cmd import exe
from loktar.cmd import exec_with_output_capture
from loktar.decorators import retry
from loktar.exceptions import CIBuildPackageFail
from loktar.plugin import ComplexPlugin


def run(*args, **kwargs):
    """This is a wrapper for running the plugin

    """
    try:
        return NPM(args[0], args[1]).run()
    except IndexError:
        print(NPM.__init__.__doc__)
        raise


class NPM(ComplexPlugin):
        def __init__(self, artifact_info, remote):
            """Plugin for building npm package

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
                10: self.bump_version,
                20: self.get_new_version,
                30: self.build,
                40: self.release
            }

            with self.cwd(self.path):
                rc, output = exec_with_output_capture("ls", remote=remote)
                if not rc:
                    raise OSError(output.join("\n"))
                else:
                    if "package.json" not in output:
                        rc, output = exec_with_output_capture("dirname $(find * -name package.json)", remote=remote)
                        if not rc:
                            raise CIBuildPackageFail("Can't find package.json")
                        else:
                            self.path = "{}/{}/".format(self.path, output[0])

        def run(self):
            """Default method for running the timeline

            """
            self._run()
            return {
                "version": self.share_memory["latest_version"]
            }

        def bump_version(self):
            """Get the next version for the current package

            """
            npm_version = "npm version {}".format(self.artifact_info.get("build_info", {}).get("bump_version", "minor")
                                                  if self.artifact_info["mode"] == "master" else
                                                  self.artifact_info.get("build_info", {}).get("bump_snapshot",
                                                                                               "prerelease"))

            with self.cwd(self.path):
                if not exe(npm_version, remote=self.remote):
                    raise CIBuildPackageFail("Failed to update the version")

        def get_new_version(self):
            self.share_memory["latest_version"] = json.loads(open(self.path + "package.json").read())["version"]

        def build(self):
            if self.artifact_info.get("build_info", {}).get("build_script", True):
                with self.cwd(self.path):
                    if not exe("npm build", remote=self.remote):
                        raise CIBuildPackageFail("Failed to publish the package")

        @retry
        def release(self):
            """Create & upload the package

            """
            with self.cwd(self.path):
                if not exe("npm publish", remote=self.remote):
                    raise CIBuildPackageFail("Failed to publish the package")
