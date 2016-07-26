import pytest

from loktar.exceptions import CIBuildPackageFail
from loktar.plugins.artifact.docker import QuayClient
from loktar.plugins.artifact.docker import QuayError
from loktar.plugins.artifact.docker import run
from loktar.plugins.artifact.docker import Docker


@pytest.fixture(autouse=True)
def os_environ(mocker):
    environ = dict(
        QUAY_HOST="https://myquay.io",
        QUAY_TOKEN="my_quay_token",
        QUAY_NAMESPACE="foobar_enterprise"
    )
    mocker.patch.dict("os.environ", environ)
    return environ


@pytest.mark.parametrize("mode", ["master", "foobar"])
@pytest.mark.parametrize("remote", [True, False])
@pytest.mark.parametrize("build_type", ["url", "trigger"])
def test_plugins_docker(mocker, mode, remote, build_type):
    mocker.patch("loktar.plugins.artifact.docker.QuayClient")
    mocker.patch("loktar.plugins.artifact.docker.exe")
    mocker.patch("loktar.plugin.exe")
    mocker.patch("loktar.plugins.artifact.docker.store_artifact", return_value="store:@:the_artifact.zip")
    mocker.patch("loktar.plugins.artifact.docker.SwaggerClient")

    run({
        "pkg_name": "foobar",
        "mode": mode,
        "package_location": "/tmp",
        "build_info": {
            "registry_type": "quay",
            "build_type": build_type,
            "storage_type": "s3",
            "trigger_service": "github"
        }
    }, remote)


@pytest.mark.parametrize("mode", ["master", "foobar"])
@pytest.mark.parametrize("remote", [True, False])
@pytest.mark.parametrize("build_type", ["url", "trigger"])
def test_plugins_docker_fail_on_init(mocker, mode, remote, build_type):
    mocker.patch("loktar.plugins.artifact.docker.QuayClient")
    mocker.patch("loktar.plugins.artifact.docker.exe")
    mocker.patch("loktar.plugin.exe")
    mocker.patch("loktar.plugins.artifact.docker.store_artifact", return_value="store:@:the_artifact.zip")
    mocker.patch("loktar.plugins.artifact.docker.SwaggerClient")

    error_message = "the registry : 'best registry for ever' is not managed, create a pr for integrate this registry"

    with pytest.raises(CIBuildPackageFail) as excinfo:
        run({
            "pkg_name": "foobar",
            "mode": mode,
            "package_location": "/tmp",
            "build_info": {
                "registry_type": "best registry for ever",
                "build_type": build_type,
                "storage_type": "s3",
                "trigger_service": "github"
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

    with pytest.raises(CIBuildPackageFail):
        run({
            "pkg_name": "foobar",
            "mode": mode,
            "package_location": "/tmp",
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
            "pkg_name": "foobar",
            "mode": mode,
            "package_location": "/tmp",
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
            raise QuayError()

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
            "pkg_name": "foobar",
            "mode": mode,
            "package_location": "/tmp",
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
