from flexmock import flexmock
import pytest

from loktar.exceptions import CIBuildPackageFail
from loktar.plugins.artifact import npm


@pytest.mark.parametrize("remote", [True, False])
@pytest.mark.parametrize("mode", ["master", "foobranch"])
@pytest.mark.parametrize("ci_payload", [
    {
        "artifact_name": "foobar",
        "artifact_root_location": "/tmp",
        "artifact_type": "npm",
    }
])
def test_plugins_npm_bump_version(remote, mode, ci_payload):
    ci_payload["mode"] = mode
    npm_version = "npm version {}".format("minor" if mode == "master" else "prerelease")

    flexmock(npm) \
        .should_receive("exe") \
        .with_args(npm_version, remote=remote) \
        .and_return(True)

    plugin = npm.NPM(ci_payload, remote)
    plugin.bump_version()


@pytest.mark.parametrize("remote", [True, False])
@pytest.mark.parametrize("mode", ["master", "foobranch"])
@pytest.mark.parametrize("ci_payload", [
    {
        "artifact_name": "foobar",
        "artifact_root_location": "/tmp",
        "artifact_type": "npm",
    }
])
def test_plugins_npm_build(remote, mode, ci_payload):
    ci_payload["mode"] = mode

    flexmock(npm) \
        .should_receive("exe") \
        .with_args("npm build", remote=remote) \
        .and_return(True)

    plugin = npm.NPM(ci_payload, remote)
    plugin.build()


@pytest.mark.parametrize("remote", [True, False])
@pytest.mark.parametrize("mode", ["master", "foobranch"])
@pytest.mark.parametrize("ci_payload", [
    {
        "artifact_name": "foobar",
        "artifact_root_location": "/tmp",
        "artifact_type": "npm",
    }
])
def test_plugins_npm_publish(remote, mode, ci_payload):
    ci_payload["mode"] = mode

    flexmock(npm) \
        .should_receive("exe") \
        .with_args("npm publish", remote=remote) \
        .and_return(True)

    plugin = npm.NPM(ci_payload, remote)
    plugin.release()


@pytest.mark.parametrize("remote", [True, False])
@pytest.mark.parametrize("mode", ["master", "foobranch"])
@pytest.mark.parametrize("ci_payload", [
    {
        "artifact_name": "foobar",
        "artifact_root_location": "/tmp",
        "artifact_type": "npm",
    }
])
def test_plugins_npm_bump_version_fail(remote, mode, ci_payload):
    ci_payload["mode"] = mode
    npm_version = "npm version {}".format("minor" if mode == "master" else "prerelease")

    flexmock(npm) \
        .should_receive("exe") \
        .with_args(npm_version, remote=remote) \
        .and_return(False)

    plugin = npm.NPM(ci_payload, remote)

    with pytest.raises(CIBuildPackageFail):
        plugin.bump_version()


@pytest.mark.parametrize("remote", [True, False])
@pytest.mark.parametrize("mode", ["master", "foobranch"])
@pytest.mark.parametrize("ci_payload", [
    {
        "artifact_name": "foobar",
        "artifact_root_location": "/tmp",
        "artifact_type": "npm",
    }
])
def test_plugins_npm_build_fail(remote, mode, ci_payload):
    ci_payload["mode"] = mode

    flexmock(npm) \
        .should_receive("exe") \
        .with_args("npm build", remote=remote) \
        .and_return(False)

    plugin = npm.NPM(ci_payload, remote)

    with pytest.raises(CIBuildPackageFail):
        plugin.build()


@pytest.mark.parametrize("remote", [True, False])
@pytest.mark.parametrize("mode", ["master", "foobranch"])
@pytest.mark.parametrize("ci_payload", [
    {
        "artifact_name": "foobar",
        "artifact_root_location": "/tmp",
        "artifact_type": "npm",
    }
])
def test_plugins_npm_publish_fail(remote, mode, ci_payload):
    ci_payload["mode"] = mode

    flexmock(npm) \
        .should_receive("exe") \
        .with_args("npm publish", remote=remote) \
        .and_return(False)

    plugin = npm.NPM(ci_payload, remote)

    with pytest.raises(CIBuildPackageFail):
        plugin.release()
