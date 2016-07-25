from quay_client import QuayClient
from quay_client import QuayError
from uuid import uuid4

from loktar.cmd import exe
from loktar.environment import QUAY
from loktar.exceptions import CIBuildPackageFail
from loktar.plugin import ComplexPlugin
from loktar.store import store_artifact


def run(*args, **kwargs):
    """This is a wrapper for running the plugin

    """
    try:
        Docker(*args)
    except TypeError:
        print(Docker.__init__.__doc__)
        raise


class Docker(object):
        def __init__(self, package_info, remote):
            if package_info["build_info"]["registry_type"] == "quay":
                _Quay(package_info, remote).run()
            else:
                raise CIBuildPackageFail("the registry : '{}' is not managed, create a pr for integrate this registry"
                                         .format(package_info["build_info"]["registry_type"]))


class _Quay(ComplexPlugin):
        def __init__(self, package_info, remote):
            """Plugin for building docker container on quay registry

                Args:
                    package_info (dict): Contains information about the package to execute inside the plugin
                    remote (bool): Define if the plugin will be execute in remote or not

                Raises:
                    CIBuildPackageFail: when one of the steps for packaging or uploading the package failed
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
                11: self.get_next_version,
                31: self.create_archive,
                51: self.store_archive,
                71: self.trigger_build,
                91: self.wait_build
            }

            self.quay = QuayClient()

        def run(self):
            """Default method for running the timeline

            """
            self._run()

        def get_next_version(self):
            """Get the next version for the current artifact

            """
            if self.package_info["mode"] == "master":
                versions = [int(tags)
                            for tags in self.quay.get_tags(self.package_info["pkg_name"], limit=QUAY["limit"])
                            if tags.isdigit()]
                versions.sort(reverse=True)
                try:
                    self.share_memory["latest_version"] = versions[0] + 1
                except IndexError:
                    self.share_memory["latest_version"] = 1
            else:
                self.share_memory["latest_version"] = self.package_info["mode"]

        def create_archive(self):
            """Create a zip archive for the quay build

            """
            archive_name = str(uuid4()) + ".zip"
            zip_command = "zip -r {} *".format(archive_name)
            with self.cwd(self.path):
                if not exe(zip_command, remote=self.remote):
                    raise CIBuildPackageFail("the command : {} executed in the directory {} return False"
                                             .format(zip_command, self.path))

            self.share_memory["archive_for_build"] = self.path + "/" + archive_name

        def store_archive(self):
            """Store the zip archive on a location where quay can fetch it

            """
            store_artifact(self.package_info["build_info"]["storage_type"], self.share_memory["archive_for_build"])
            self.share_memory["archive_url"] = "not implemented"

        def trigger_build(self):
            """Trigger the build

            """
            if self.package_info["build_info"]["build_type"] == "url":
                extra_tags = [self.share_memory["latest_version"]] if self.package_info["mode"] == "master" else []

                self.share_memory["build_id"] = self.quay.start_build_url(self.package_info["pkg_name"],
                                                                          self.package_info["mode"],
                                                                          self.share_memory["archive_url"],
                                                                          extra_tags=extra_tags)

            elif self.package_info["build_info"]["build_type"] == "trigger":
                trigger_id = self.quay.find_trigger(self.package_info["pkg_name"],
                                                    service=self.package_info["build_info"]["trigger_service"])

                self.share_memory["build_id"] = self.quay.start_build_trigger(self.package_info["pkg_name"],
                                                                              self.package_info["mode"],
                                                                              trigger_id)

            else:
                raise CIBuildPackageFail("Unknown build type: {}, only url or trigger is supported")

        def wait_build(self):
            """Wait the end of the build

            """
            try:
                build_time = self.quay.wait_build_complete(self.package_info["pkg_name"], self.share_memory["build_id"])
            except QuayError as e:
                raise CIBuildPackageFail(str(e))

            self.logger.info("The build for the artifact: {} took {}s has to be built on the branch {}"
                             .format(self.package_info["pkg_name"],
                                     build_time,
                                     self.package_info["mode"]))
