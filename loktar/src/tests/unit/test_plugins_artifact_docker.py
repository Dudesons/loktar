import pytest
import os

from loktar.exceptions import CIBuildPackageFail
from loktar.plugins.artifact.docker import GuayError
from loktar.plugins.artifact.docker import QuayClient
from loktar.plugins.artifact.docker import QuayError
from loktar.plugins.artifact.docker import run
from loktar.plugins.artifact.docker import Docker


@pytest.fixture(autouse=True)
def os_environ(mocker):
    environ = dict(
        LOKTAR_CI_HOST="https://myAwsomeCI",
        LOKTAR_GUAY_TIMEOUT="1",
        QUAY_HOST="https://myquay.io",
        QUAY_TOKEN="my_quay_token",
        QUAY_NAMESPACE="foobar_enterprise"
    )
    mocker.patch.dict("os.environ", environ)
    return environ


@pytest.mark.parametrize("mode", ["master", "foobar"])
@pytest.mark.parametrize("remote", [True, False])
@pytest.mark.parametrize("build_type", ["url", "trigger"])
def test_plugins_docker_quay(mocker, mode, remote, build_type):
    mocker.patch("loktar.plugins.artifact.docker.QuayClient")
    mocker.patch("loktar.plugins.artifact.docker.exe")
    mocker.patch("loktar.plugin.exe")
    mocker.patch("loktar.plugins.artifact.docker.store_artifact", return_value="store:@:the_artifact.zip")
    mocker.patch("loktar.plugins.artifact.docker.SwaggerClient")

    run({
        "artifact_name": "foobar",
        "mode": mode,
        "artifact_root_location": "/tmp",
        "build_info": {
            "registry_type": "quay",
            "build_type": build_type,
            "storage_type": "s3",
            "trigger_service": "github"
        }
    }, remote)


@pytest.mark.parametrize("mode", ["master", "foobar"])
@pytest.mark.parametrize("remote", [True, False])
@pytest.mark.parametrize("status", ["success", "faillure"])
def test_plugins_docker_guay(mocker, mode, status, remote):
    class FakeClient(object):
        def __init__(self):
            class IMAGE(object):
                def __init__(self):
                    pass

                def DockerImage(self, *args, **kwargs):
                    class ResultDockerImage(object):
                        def __init__(self):
                            pass

                        def result(self):
                            class Result(object):
                                def __init__(self):
                                    self.latest_version = 1

                            return Result()

                    return ResultDockerImage()

            class BUILD(object):
                def __init__(self):
                    pass

                def StartBuild(self, *args, **kwargs):
                    class ResultStartBuild(object):
                        def __init__(self):
                            pass

                        def result(self):
                            class Result(object):
                                def __init__(self):
                                    self.build_id = "foo"

                            return Result()

                    return ResultStartBuild()

                def BuildStatus(self, *args, **kwargs):
                    class ResultBuildStatus(object):
                        def __init__(self):
                            pass

                        def result(self):
                            class Result(object):
                                def __init__(self):
                                    self.build_id = "foo"
                                    self.status = status
                                    self.content = ["step1", "step2"]

                            return Result()

                    return ResultBuildStatus()

            class GetArtifact(object):
                def __init__(self):
                    pass

                def storage_proxy_get_artifact(self, *args, **kwargs):
                    class Result_storage_proxy_get_artifact(object):
                        def __init__(self):
                            pass

                        def result(self):
                            return "/dadasdas.tar.xz"

                    return Result_storage_proxy_get_artifact()

            self.IMAGE = IMAGE()
            self.BUILD = BUILD()
            self.get_artifact = GetArtifact()

    def FakeSwaggerClient():
        return FakeClient()

    mocker.patch("loktar.plugins.artifact.docker.exe")
    mocker.patch("loktar.plugin.exe")
    mocker.patch("loktar.plugins.artifact.docker.store_artifact", return_value="store:@:the_artifact.tar.xz")
    mocker.patch("loktar.plugins.artifact.docker.SwaggerClient.from_url", return_value=FakeSwaggerClient())

    if status == "success":
        run({
            "artifact_name": "foobar",
            "mode": mode,
            "artifact_root_location": "/tmp",
            "commit_id": "1dsd1w1dgfdg",
            "build_info": {
                "registry_type": "guay",
                "registry_prefix": "my_org_registry",
                "storage_type": "s3",
            }
        }, remote)
    else:
        with pytest.raises(GuayError) as excinfo:
            run({
                "artifact_name": "foobar",
                "mode": mode,
                "artifact_root_location": "/tmp",
                "commit_id": "1dsd1w1dgfdg",
                "build_info": {
                    "registry_type": "guay",
                    "registry_prefix": "my_org_registry",
                    "storage_type": "s3",
                }
            }, remote)

            assert str(excinfo) == "GuayError: GuayError: The build failed, build_id: foo"


@pytest.mark.parametrize("mode", ["master", "foobar"])
@pytest.mark.parametrize("remote", [True, False])
def test_plugins_docker_fail_on_init(mocker, mode, remote):
    mocker.patch("loktar.plugins.artifact.docker.QuayClient")
    mocker.patch("loktar.plugins.artifact.docker.exe")
    mocker.patch("loktar.plugin.exe")
    mocker.patch("loktar.plugins.artifact.docker.store_artifact", return_value="store:@:the_artifact.zip")
    mocker.patch("loktar.plugins.artifact.docker.SwaggerClient")

    error_message = "the registry : 'best registry for ever' is not managed, create a pr for integrate this registry"

    with pytest.raises(CIBuildPackageFail) as excinfo:
        run({
            "artifact_name": "foobar",
            "mode": mode,
            "artifact_root_location": "/tmp",
            "build_info": {
                "registry_type": "best registry for ever",
            }
        }, remote)

        assert str(excinfo) == error_message


@pytest.mark.parametrize("mode", ["master", "foobar"])
@pytest.mark.parametrize("remote", [True, False])
@pytest.mark.parametrize("build_type", ["url", "trigger"])
def test_plugins_docker_fail_on_create_archive(mocker, mode, remote, build_type):
    mocker.patch("loktar.plugins.artifact.docker.QuayClient")
    mocker.patch("loktar.plugins.artifact.docker.exe", return_value=False)
    mocker.patch("loktar.plugin.exe")
    mocker.patch("loktar.plugins.artifact.docker.store_artifact", return_value="store:@:the_artifact.zip")
    mocker.patch("loktar.plugins.artifact.docker.SwaggerClient")

    if build_type == "url":
        with pytest.raises(CIBuildPackageFail):
            run({
                "artifact_name": "foobar",
                "mode": mode,
                "artifact_root_location": "/tmp",
                "build_info": {
                    "registry_type": "quay",
                    "build_type": build_type,
                    "storge_type": "s3",
                    "trigger_service": "github"
                }
            }, remote)

        with pytest.raises(CIBuildPackageFail):
            run({
                "artifact_name": "foobar",
                "mode": mode,
                "artifact_root_location": "/tmp",
                "build_info": {
                    "registry_type": "guay",
                    "registry_prefix": "my_org_registry",
                    "storge_type": "s3",
                }
            }, remote)
    else:
        run({
            "artifact_name": "foobar",
            "mode": mode,
            "artifact_root_location": "/tmp",
            "build_info": {
                "registry_type": "quay",
                "build_type": build_type,
                "storge_type": "s3",
                "trigger_service": "github"
            }
        }, remote)


@pytest.mark.parametrize("mode", ["master", "foobar"])
@pytest.mark.parametrize("remote", [True, False])
def test_plugins_docker_fail_on_trigger_build(mocker, mode, remote):
    mocker.patch("loktar.plugins.artifact.docker.QuayClient")
    mocker.patch("loktar.plugins.artifact.docker.exe")
    mocker.patch("loktar.plugin.exe")
    mocker.patch("loktar.plugins.artifact.docker.store_artifact", return_value="store:@:the_artifact.zip")
    mocker.patch("loktar.plugins.artifact.docker.SwaggerClient")

    with pytest.raises(CIBuildPackageFail):
        run({
            "artifact_name": "foobar",
            "mode": mode,
            "artifact_root_location": "/tmp",
            "build_info": {
                "registry_type": "quay",
                "build_type": "wtf_trigger",
                "storage_type": "s3",
                "trigger_service": "github"
            }
        }, remote)


@pytest.mark.parametrize("mode", ["master", "foobar"])
@pytest.mark.parametrize("remote", [True, False])
@pytest.mark.parametrize("build_type", ["url", "trigger"])
def test_plugins_docker_fail_on_wait_build(mocker, mode, remote, build_type):

    class FakeQuayClient(object):
        def __init__(self):
            pass

        def get_tags(self, *args, **kwargs):
            return [
                    "a"
                    "w",
                    "1",
                    "4"
            ]

        def wait_build_complete(self, *args, **kwargs):
            raise QuayError("Fake error")

        def find_trigger(self, *args, **kwargs):
            pass

        def start_build_trigger(self, *args, **kwargs):
            pass

        def start_build_url(self, *args, **kwargs):
            pass

    mocker.patch("loktar.plugins.artifact.docker.QuayClient", side_effect=FakeQuayClient)
    mocker.patch("loktar.plugins.artifact.docker.exe")
    mocker.patch("loktar.plugin.exe")
    mocker.patch("loktar.plugins.artifact.docker.store_artifact", return_value="store:@:the_artifact.zip")
    mocker.patch("loktar.plugins.artifact.docker.SwaggerClient")

    with pytest.raises(CIBuildPackageFail):
        run({
            "artifact_name": "foobar",
            "mode": mode,
            "artifact_root_location": "/tmp",
            "build_info": {
                "registry_type": "quay",
                "build_type": build_type,
                "storage_type": "s3",
                "trigger_service": "github"
            }
        }, remote)


def test_plugins_docker_fail_on_call():
    with pytest.raises(TypeError):
        output = run()
        assert output == Docker.__init__.__doc__
