from bravado.client import SwaggerClient
from bravado.exception import HTTPError
from bravado_core.exception import SwaggerError
from bravado_core.exception import SwaggerSchemaError
from bravado_core.exception import SwaggerValidationError
from quay_client import QuayClient
from quay_client import QuayError
import time
from uuid import uuid4

from loktar.cmd import exe
from loktar.constants import AWS
from loktar.constants import CI
from loktar.constants import GUAY
from loktar.constants import QUAY
from loktar.constants import STORAGE_PROXY
from loktar.exceptions import CIBuildPackageFail
from loktar.exceptions import GuayError
from loktar.exceptions import StorageProxyError
from loktar.plugin import ComplexPlugin
from loktar.store import store_artifact


def run(*args, **kwargs):
    """This is a wrapper for running the plugin

    """
    try:
        plugin = Docker(*args)
        return plugin.get_result()
    except TypeError:
        print(Docker.__init__.__doc__)
        raise


class Docker(object):
        def __init__(self, package_info, remote):
            if package_info["build_info"]["registry_type"] == "quay":
                self.__result = _Quay(package_info, remote).run()
            elif package_info["build_info"]["registry_type"] == "guay":
                self.__result = _Guay(package_info, remote).run()
            else:
                raise CIBuildPackageFail("the registry : '{}' is not managed, create a pr for integrate this registry"
                                         .format(package_info["build_info"]["registry_type"]))

        def get_result(self):
            return self.__result


class _Guay(ComplexPlugin):
    def __init__(self, package_info, remote):
        """Plugin for building docker container on guay registry

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

        self.guay = SwaggerClient.from_url("{}/swagger.json".format(GUAY["host"]))
        self.storage_proxy = SwaggerClient.from_url("{}:{}/v1/swagger.json".format(STORAGE_PROXY["host"],
                                                                                   STORAGE_PROXY["port"]))

    def run(self):
        """Default method for running the timeline

        """
        self._run()
        return {
            "version": self.share_memory["latest_version"]
        }

    def get_next_version(self):
        """Get the next version for the current artifact

        """
        if self.package_info["mode"] == "master":
            try:
                image_info = self.guay.IMAGE.DockerImage(image_name=self.package_info["artifact_name"]).result()
            except (SwaggerError, SwaggerSchemaError, SwaggerValidationError, HTTPError) as e:
                raise GuayError(str(e))
            self.share_memory["latest_version"] = str(image_info.latest_version + 1)
        else:
            self.share_memory["latest_version"] = self.package_info["mode"]

        self.logger.info("The next version for the current artifact is {} on branch {}"
                         .format(self.share_memory["latest_version"], self.package_info["mode"]))

    def create_archive(self):
        """Create a zip archive for the quay build

        """
        archive_name = str(uuid4()) + ".tar.xz"
        compress_command = "tar Jcvf  {} .".format(archive_name)
        with self.cwd(self.path):
            if not exe(compress_command, remote=self.remote):
                raise CIBuildPackageFail("the command : {} executed in the directory {} return False"
                                         .format(compress_command, self.path))

        self.share_memory["archive_for_build"] = self.path + "/" + archive_name
        self.logger.info("Tar archive built")

    def store_archive(self):
        """Store the zip archive on a location where quay can fetch it

        """
        self.logger.info("Uploading artifact: {} to {} storage"
                         .format(self.share_memory["archive_for_build"],
                                 self.package_info["build_info"]["storage_type"]))

        try:
            artifact_ref = store_artifact(self.package_info["build_info"]["storage_type"],
                                          self.share_memory["archive_for_build"])
        except (SwaggerError, SwaggerSchemaError, SwaggerValidationError, HTTPError) as e:
            raise GuayError(str(e))

        self.logger.info("Artifact uploaded, ref: {}".format(artifact_ref))

        storage_method, artifact_path = artifact_ref.split(":@:")

        try:
            self.share_memory["archive_url"] = self.storage_proxy.get_artifact.storage_proxy_get_artifact(
                storage_backend=storage_method,
                bucket_name=AWS["BUCKET"],
                artifact_name=artifact_path
            ).result()
        except (SwaggerError, SwaggerSchemaError, SwaggerValidationError, HTTPError) as e:
            raise StorageProxyError(str(e))

        self.logger.info("Storage proxy requested")

    def trigger_build(self):
        """Trigger the build

        """
        external_archive_url = "{}/{}".format(CI["external_fqdn"], self.share_memory["archive_url"])
        try:
            self.share_memory["build_id"] = self.guay.BUILD.StartBuild(build_request={
                "build_id": str(uuid4()),
                "image": self.package_info["artifact_name"],
                "version": self.share_memory["latest_version"],
                "archive_url": external_archive_url
            }).result().build_id
        except (SwaggerError, SwaggerSchemaError, SwaggerValidationError, HTTPError) as e:
            raise StorageProxyError(str(e))

        self.logger.info("The artifact for guay is available at: {}".format(external_archive_url))
        self.logger.info("Start build")

        self.logger.info("Building ...")
        self.logger.info("Build id: {}".format(self.share_memory["build_id"]))

    def wait_build(self):
        """Wait the end of the build

        """
        start_time = time.time()
        actual_time = time.time()
        log_position = 0
        build_result = False

        self.logger.info("Build start at: {}".format(start_time))
        self.logger.info("Build timeout set at {}".format(GUAY["timeout"]))

        while 42:
            try:
                build_status = self.guay.BUILD.BuildStatus(build_id=self.share_memory["build_id"]).result()
            except (SwaggerError, SwaggerSchemaError, SwaggerValidationError, HTTPError) as e:
                raise CIBuildPackageFail(str(e))

            self.logger.info("build_id={} build_status={}".format(build_status.build_id, build_status.status))
            if len(build_status.content) > log_position:
                for log in xrange(log_position, len(build_status.content)):
                    self.logger.info(log)

            if build_status.status == "success":
                build_result = True
                break

            if "faillure" in build_status.status:
                build_result = False
                break

            if actual_time - start_time >= GUAY["timeout"]:
                raise GuayError("Build timeout, build_id: {}".format(build_status.build_id))

            time.sleep(10)
            actual_time = time.time()

        if not build_result:
            raise GuayError("The build failed, build_id: {}".format(build_status.build_id))

        build_time = time.time() - start_time
        self.logger.info("The build for the artifact: {} took {}s has to be built on the branch {}"
                         .format(self.package_info["artifact_name"],
                                 build_time,
                                 self.package_info["mode"]))


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
            self.storage_proxy = SwaggerClient.from_url("{}:{}/v1/swagger.json".format(STORAGE_PROXY["host"],
                                                                                       STORAGE_PROXY["port"]))

        def run(self):
            """Default method for running the timeline

            """
            self._run()
            return {
                "version": self.share_memory["latest_version"]
            }

        def get_next_version(self):
            """Get the next version for the current artifact

            """
            if self.package_info["mode"] == "master":
                versions = [int(tags)
                            for tags in self.quay.get_tags(self.package_info["artifact_name"], limit=QUAY["limit"])
                            if tags.isdigit()]
                versions.sort(reverse=True)
                try:
                    self.share_memory["latest_version"] = str(int(versions[0]) + 1)
                except IndexError:
                    self.share_memory["latest_version"] = "1"
            else:
                self.share_memory["latest_version"] = self.package_info["mode"]

            self.logger.info("The next version for the current package is {} on branch {}"
                             .format(self.share_memory["latest_version"], self.package_info["mode"]))

        def create_archive(self):
            """Create a zip archive for the quay build

            """
            if self.package_info["build_info"]["build_type"] == "url":
                archive_name = str(uuid4()) + ".zip"
                zip_command = "zip -r {} *".format(archive_name)
                with self.cwd(self.path):
                    if not exe(zip_command, remote=self.remote):
                        raise CIBuildPackageFail("the command : {} executed in the directory {} return False"
                                                 .format(zip_command, self.path))

                self.share_memory["archive_for_build"] = self.path + "/" + archive_name
                self.logger.info("Zip archive built")
            else:
                self.logger.info("Zip archive skipped, it' only for url build")

        def store_archive(self):
            """Store the zip archive on a location where quay can fetch it

            """
            if self.package_info["build_info"]["build_type"] == "url":
                self.logger.info("Uploading artifact: {} to {} storage"
                                 .format(self.share_memory["archive_for_build"],
                                         self.package_info["build_info"]["storage_type"]))

                artifact_ref = store_artifact(self.package_info["build_info"]["storage_type"],
                                              self.share_memory["archive_for_build"])

                self.logger.info("Artifact uploaded, ref: {}".format(artifact_ref))

                storage_method, artifact_path = artifact_ref.split(":@:")

                self.share_memory["archive_url"] = self.storage_proxy.get_artifact.storage_proxy_get_artifact(
                    storage_backend=storage_method,
                    bucket_name=AWS["BUCKET"],
                    artifact_name=artifact_path
                ).result()

                self.logger.info("Storage proxy requested")
            else:
                self.logger.info("Store archive skipped, it' only for url build")

        def trigger_build(self):
            """Trigger the build

            """
            if self.package_info["build_info"]["build_type"] == "url":
                extra_tags = [self.share_memory["latest_version"]] if self.package_info["mode"] == "master" else []
                external_archive_url = "{}/{}".format(CI["external_fqdn"], self.share_memory["archive_url"])

                self.logger.info("The artifact for quay is available at: {}".format(external_archive_url))
                self.logger.info("Start build")

                self.share_memory["build_id"] = self.quay.start_build_url(self.package_info["artifact_name"],
                                                                          self.package_info["mode"],
                                                                          external_archive_url,
                                                                          extra_tags=extra_tags)

            elif self.package_info["build_info"]["build_type"] == "trigger":
                self.logger.info("Searching trigger ...")

                trigger_id = self.quay.find_trigger(self.package_info["artifact_name"],
                                                    service=self.package_info["build_info"]["trigger_service"])

                self.logger.info("Trigger id: {}".format(trigger_id))
                self.logger.info("Start build")

                self.share_memory["build_id"] = self.quay.start_build_trigger(self.package_info["artifact_name"],
                                                                              self.package_info["mode"],
                                                                              trigger_id)

            else:
                raise CIBuildPackageFail("Unknown build type: {}, only url or trigger is supported")

            self.logger.info("Building ...")
            self.logger.info("Build id: {}".format(self.share_memory["build_id"]))

        def wait_build(self):
            """Wait the end of the build

            """
            try:
                build_time = self.quay.wait_build_complete(self.package_info["artifact_name"], self.share_memory["build_id"])
            except QuayError as e:
                raise CIBuildPackageFail(str(e))

            self.logger.info("The build for the artifact: {} took {}s has to be built on the branch {}"
                             .format(self.package_info["artifact_name"],
                                     build_time,
                                     self.package_info["mode"]))
